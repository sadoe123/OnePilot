import aioodbc
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


class MSSQLConnector(BaseConnector):
    """Connecteur pour bases de données Microsoft SQL Server."""

    def __init__(self, connector_id: str, name: str, config: Dict[str, Any]):
        super().__init__(
            connector_id=connector_id,
            name=name,
            connector_type=ConnectorType.SQL,
            config=config
        )
        self._pool: Optional[aioodbc.Pool] = None
        self.default_schema = config.get("schema", "dbo")

    def _get_connection_string(self) -> str:
        """Construit la chaîne de connexion ODBC."""
        return (
            f"Driver={{ODBC Driver 17 for SQL Server}};"
            f"Server={self.config['host']},{self.config.get('port', 1433)};"
            f"Database={self.config['database']};"
            f"UID={self.config['user']};"
            f"PWD={self.config['password']};"
        )

    async def connect(self) -> bool:
        try:
            self.status = ConnectorStatus.CONNECTING
            logger.info(f"Connexion à MSSQL: {self.config['host']}:{self.config.get('port', 1433)}")

            dsn = self._get_connection_string()
            self._pool = await aioodbc.create_pool(dsn=dsn, minsize=2, maxsize=10)

            async with self._pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT @@VERSION")
                    version = await cursor.fetchone()
                    logger.info(f"Connecté: {version[0][:50]}...")

            self.status = ConnectorStatus.CONNECTED
            self.last_connected = datetime.now()
            return True

        except Exception as e:
            self.status = ConnectorStatus.ERROR
            raise ConnectionFailedException(
                f"Échec connexion MSSQL: {str(e)}",
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
            dsn = self._get_connection_string()
            conn = await aioodbc.connect(dsn=dsn, timeout=10)
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT 1")
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
                async with conn.cursor() as cursor:
                    # Récupérer toutes les tables
                    await cursor.execute(f"""
                        SELECT TABLE_SCHEMA, TABLE_NAME
                        FROM INFORMATION_SCHEMA.TABLES
                        WHERE TABLE_SCHEMA = '{self.default_schema}'
                        AND TABLE_TYPE = 'BASE TABLE'
                        ORDER BY TABLE_NAME
                    """)
                    tables_rows = await cursor.fetchall()

                    tables = []
                    for row in tables_rows:
                        schema_name = row[0]
                        table_name = row[1]
                        
                        # Colonnes
                        await cursor.execute(f"""
                            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                            FROM INFORMATION_SCHEMA.COLUMNS
                            WHERE TABLE_SCHEMA = '{schema_name}' 
                            AND TABLE_NAME = '{table_name}'
                            ORDER BY ORDINAL_POSITION
                        """)
                        cols = await cursor.fetchall()

                        # Compter les lignes
                        await cursor.execute(f"SELECT COUNT(*) FROM {schema_name}.{table_name}")
                        count_row = await cursor.fetchone()
                        count = count_row[0] if count_row else 0

                        tables.append({
                            "name": table_name,
                            "schema": schema_name,
                            "columns": [
                                {
                                    "name": c[0],
                                    "type": c[1],
                                    "nullable": c[2] == "YES"
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
                async with conn.cursor() as cursor:
                    await cursor.execute(query)
                    rows = await cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            raise QueryExecutionException(
                f"Échec requête: {str(e)}",
                details={"query": query}
            )