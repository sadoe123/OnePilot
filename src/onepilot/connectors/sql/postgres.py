import asyncpg
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from ..base import BaseConnector, ConnectorType, ConnectorStatus
from ...core.exceptions import (
    ConnectionFailedException,
    QueryExecutionException,
    SchemaDiscoveryException
)

logger = logging.getLogger(__name__)


class PostgresConnector(BaseConnector):
    """Connecteur pour bases de données PostgreSQL."""

    def __init__(self, connector_id: str, name: str, config: Dict[str, Any]):
        super().__init__(
            connector_id=connector_id,
            name=name,
            connector_type=ConnectorType.SQL,
            config=config
        )
        self._pool: Optional[asyncpg.Pool] = None
        self.default_schema = config.get("schema", "public")

    async def connect(self) -> bool:
        try:
            self.status = ConnectorStatus.CONNECTING
            logger.info(f"Connexion à PostgreSQL: {self.config['host']}:{self.config.get('port', 5432)}")

            self._pool = await asyncpg.create_pool(
                host=self.config["host"],
                port=self.config.get("port", 5432),
                database=self.config["database"],
                user=self.config["user"],
                password=self.config["password"],
                min_size=2,
                max_size=10,
                command_timeout=60
            )

            # Test rapide
            async with self._pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                logger.info(f"Connecté: {version[:50]}")

            self.status = ConnectorStatus.CONNECTED
            self.last_connected = datetime.now()
            return True

        except Exception as e:
            self.status = ConnectorStatus.ERROR
            raise ConnectionFailedException(
                f"Échec connexion PostgreSQL: {str(e)}",
                details={"host": self.config.get("host")}
            )

    async def disconnect(self) -> bool:
        try:
            if self._pool:
                await self._pool.close()
                self._pool = None
            self.status = ConnectorStatus.DISCONNECTED
            logger.info(f"Déconnecté: {self.name}")
            return True
        except Exception as e:
            logger.error(f"Erreur déconnexion: {str(e)}")
            return False

    async def test_connection(self) -> Dict[str, Any]:
        start = datetime.now()
        try:
            conn = await asyncpg.connect(
                host=self.config["host"],
                port=self.config.get("port", 5432),
                database=self.config["database"],
                user=self.config["user"],
                password=self.config["password"],
                timeout=10
            )
            await conn.fetchval("SELECT 1")
            await conn.close()
            latency = (datetime.now() - start).total_seconds() * 1000
            return {"success": True, "message": "Connexion OK", "latency_ms": round(latency, 2)}
        except Exception as e:
            return {"success": False, "message": "Échec", "error": str(e)}

    async def get_schema(self) -> Dict[str, Any]:
        if not self._pool:
            raise SchemaDiscoveryException("Non connecté")
        try:
            async with self._pool.acquire() as conn:
                # Récupérer toutes les tables
                tables_rows = await conn.fetch("""
                    SELECT table_schema, table_name
                    FROM information_schema.tables
                    WHERE table_schema = $1 AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """, self.default_schema)

                tables = []
                for row in tables_rows:
                    # Colonnes de chaque table
                    cols = await conn.fetch("""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns
                        WHERE table_schema = $1 AND table_name = $2
                        ORDER BY ordinal_position
                    """, row["table_schema"], row["table_name"])

                    # Compter les lignes
                    count = await conn.fetchval(
                        f'SELECT COUNT(*) FROM {row["table_schema"]}.{row["table_name"]}'
                    )

                    tables.append({
                        "name": row["table_name"],
                        "schema": row["table_schema"],
                        "columns": [
                            {
                                "name": c["column_name"],
                                "type": c["data_type"],
                                "nullable": c["is_nullable"] == "YES"
                            }
                            for c in cols
                        ],
                        "row_count": count
                    })

                return {
                    "connector_id": self.connector_id,
                    "database": self.config["database"],
                    "tables": tables,
                    "discovered_at": datetime.now().isoformat()
                }
        except Exception as e:
            raise SchemaDiscoveryException(f"Échec découverte schéma: {str(e)}")

    async def execute_query(self, query: str, params: Dict = None) -> List[Dict[str, Any]]:
        if not self._pool:
            raise QueryExecutionException("Non connecté")
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query)
                return [dict(row) for row in rows]
        except Exception as e:
            raise QueryExecutionException(
                f"Échec requête: {str(e)}",
                details={"query": query}
            )