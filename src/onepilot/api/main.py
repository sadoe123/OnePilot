from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

from ..core.config import settings
from ..connectors.sql.postgres import PostgresConnector
from ..core.exceptions import ConnectorException

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Agent IA conversationnel universel pour ERP"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stockage en mémoire des connecteurs
connectors: Dict[str, PostgresConnector] = {}


# ── Schémas ────────────────────────────────────────────────
class ConnectorCreate(BaseModel):
    name: str
    host: str
    port: int = 5432
    database: str
    user: str
    password: str
    schema_name: str = "public"


class QueryRequest(BaseModel):
    connector_id: str
    query: str


# ── Endpoints ──────────────────────────────────────────────
@app.get("/")
async def root():
    return {"app": settings.app_name, "version": settings.app_version, "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy", "connectors": len(connectors)}


@app.post("/connectors")
async def create_connector(data: ConnectorCreate):
    try:
        connector_id = f"pg-{len(connectors) + 1}"
        connector = PostgresConnector(
            connector_id=connector_id,
            name=data.name,
            config={
                "host": data.host,
                "port": data.port,
                "database": data.database,
                "user": data.user,
                "password": data.password,
                "schema": data.schema_name
            }
        )
        await connector.connect()
        connectors[connector_id] = connector
        logger.info(f"Connecteur créé: {connector_id}")
        return {"success": True, "connector_id": connector_id}
    except ConnectorException as e:
        raise HTTPException(status_code=400, detail=e.message)


@app.get("/connectors")
async def list_connectors():
    return {"connectors": [c.get_status() for c in connectors.values()]}


@app.get("/connectors/{connector_id}/schema")
async def get_schema(connector_id: str):
    if connector_id not in connectors:
        raise HTTPException(status_code=404, detail="Connecteur introuvable")
    try:
        return await connectors[connector_id].get_schema()
    except ConnectorException as e:
        raise HTTPException(status_code=500, detail=e.message)


@app.post("/query")
async def execute_query(request: QueryRequest):
    if request.connector_id not in connectors:
        raise HTTPException(status_code=404, detail="Connecteur introuvable")
    try:
        from datetime import datetime
        start = datetime.now()
        results = await connectors[request.connector_id].execute_query(request.query)
        ms = (datetime.now() - start).total_seconds() * 1000
        return {"success": True, "rows": results, "count": len(results), "time_ms": round(ms, 2)}
    except ConnectorException as e:
        raise HTTPException(status_code=500, detail=e.message)