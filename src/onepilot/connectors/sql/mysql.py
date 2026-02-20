import aiomysql
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


class MySQLConnector(BaseConnector):
    """Connecteur pour bases de données MySQL."""

    def __init__(self, connector_id: str, name: str, config: Dict[str, Any]):
        super().__init__(
            connector_id=connector_id,
            name=name,
            connector_type=ConnectorType.SQL,
            config=config
        )
        self._pool: Optional[aiomysql.Pool] = None
        self.default_schema = config.get("database")

    async def connect(self) -> bool:
        try:
            self.status = ConnectorStatus.CONNECTING
            logger.info(f"Connexion à MySQL: {self.config['host']}:{self.config.get('port', 3306)}")

            self._pool = await aiomysql.create_pool(
                host=self.config["host"],
                port=self.config.get("port", 3306),
                db=self.config["database"],
                user=self.config["user"],
                password=self.config["password"],
                minsize=2,
                maxsize=10,
                autocommit=True
            )

            async with self._pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT VERSION()")
                    version = await cursor.fetchone()
                    logger.info(f"Connecté: MySQL {version[0]}")

            self.status = ConnectorStatus.CONNECTED
            self.last_connected = datetime.now()
            return True

        except Exception as e:
            self.status = ConnectorStatus.ERROR
            raise ConnectionFailedException(
                f"Échec connexion MySQL: {str(e)}",
                details={"host": self.config.get("host")}
            )

    async def disconnect(self) -> bool:
        try:
            if self._pool:
                self._pool.close()
                await self._pool.wait_closed()
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
            conn = await aiomysql.connect(
                host=self.config["host"],
                port=self.config.get("port", 3306),
                db=self.config["database"],
                user=self.config["user"],
                password=self.config["password"]
            )
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT 1")
            conn.close()
            latency = (datetime.now() - start).total_seconds() * 1000
            return {"success": True, "message": "Connexion OK", "latency_ms": round(latency, 2)}
        except Exception as e:
            return {"success": False, "message": "Échec", "error": str(e)}

    async def get_schema(self) -> Dict[str, Any]:
        if not self._pool:
            raise SchemaDiscoveryException("Non connecté")
        try:
            async with self._pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Récupérer toutes les tables
                    await cursor.execute(f"SHOW TABLES FROM {self.default_schema}")
                    tables_rows = await cursor.fetchall()

                    tables = []
                    for row in tables_rows:
                        table_name = row[0]
                        
                        # Colonnes de chaque table
                        await cursor.execute(f"DESCRIBE {self.default_schema}.{table_name}")
                        cols = await cursor.fetchall()

                        # Compter les lignes
                        await cursor.execute(f"SELECT COUNT(*) FROM {self.default_schema}.{table_name}")
                        count_row = await cursor.fetchone()
                        count = count_row[0] if count_row else 0

                        tables.append({
                            "name": table_name,
                            "schema": self.default_schema,
                            "columns": [
                                {
                                    "name": c[0],
                                    "type": c[1],
                                    "nullable": c[2] == "YES",
                                    "primary_key": c[3] == "PRI"
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
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(query)
                    rows = await cursor.fetchall()
                    return list(rows)
        except Exception as e:
            raise QueryExecutionException(
                f"Échec requête: {str(e)}",
                details={"query": query}
            )