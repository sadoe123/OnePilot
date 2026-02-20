from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Dict, Any, Union, Optional
import logging
import json
import asyncio

from ..core.config import settings
from ..connectors.sql.postgres import PostgresConnector
from ..connectors.sql.mysql import MySQLConnector
from ..connectors.sql.mssql import MSSQLConnector
from ..connectors.api.rest import RESTConnector
from ..connectors.api.odata import ODataConnector
from ..core.exceptions import ConnectorException, LLMException
from ..generation.llm_engine import llm_engine
from ..database.models import Conversation, Connector
from ..database.session import get_db
from ..core.monitoring import monitoring_service

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
connectors: Dict[str, Union[PostgresConnector, MySQLConnector, MSSQLConnector, RESTConnector, ODataConnector]] = {}


# ── Lifecycle Events ───────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    """Démarré au lancement de l'application."""
    logger.info("Starting OnePilot API...")
    # Démarrer le monitoring après un court délai
    await asyncio.sleep(5)
    await monitoring_service.start(connectors)
    logger.info("Monitoring service started")


@app.on_event("shutdown")
async def shutdown_event():
    """Arrêté à la fermeture de l'application."""
    logger.info("Stopping OnePilot API...")
    await monitoring_service.stop()
    # Fermer tous les connecteurs
    for connector in connectors.values():
        try:
            await connector.disconnect()
        except:
            pass
    logger.info("All connectors closed")


# ── Schémas ────────────────────────────────────────────────
class ConnectorCreate(BaseModel):
    name: str
    type: str = "postgres"  # postgres, mysql, mssql, rest, odata
    
    # Champs SQL
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    schema_name: str = "public"
    
    # Champs REST/OData
    base_url: Optional[str] = None
    auth_type: str = "none"  # none, bearer, basic, api_key
    token: Optional[str] = None
    api_key: Optional[str] = None
    api_key_name: str = "X-API-Key"
    username: Optional[str] = None
    health_endpoint: str = "/"
    
    # Champs OData
    service_root: str = ""


class QueryRequest(BaseModel):
    connector_id: str
    query: str


class AskRequest(BaseModel):
    connector_id: str
    question: str


# ── Endpoints ──────────────────────────────────────────────
@app.get("/")
async def root():
    return {"app": settings.app_name, "version": settings.app_version, "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy", "connectors": len(connectors)}


@app.post("/connectors")
async def create_connector(data: ConnectorCreate, db: Session = Depends(get_db)):
    try:
        import uuid
        
        connector_uuid = uuid.uuid4()
        connector_id = f"{data.type}-{len(connectors) + 1}"
        
        # Déterminer le port par défaut pour SQL
        if data.port is None and data.type in ["postgres", "mysql", "mssql"]:
            if data.type == "postgres":
                data.port = 5432
            elif data.type == "mysql":
                data.port = 3306
            elif data.type == "mssql":
                data.port = 1433
        
        # Créer le bon connecteur selon le type
        if data.type == "postgres":
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
        elif data.type == "mysql":
            connector = MySQLConnector(
                connector_id=connector_id,
                name=data.name,
                config={
                    "host": data.host,
                    "port": data.port,
                    "database": data.database,
                    "user": data.user,
                    "password": data.password
                }
            )
        elif data.type == "mssql":
            connector = MSSQLConnector(
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
        elif data.type == "rest":
            connector = RESTConnector(
                connector_id=connector_id,
                name=data.name,
                config={
                    "base_url": data.base_url,
                    "auth_type": data.auth_type,
                    "token": data.token,
                    "api_key": data.api_key,
                    "api_key_name": data.api_key_name,
                    "username": data.username,
                    "password": data.password,
                    "health_endpoint": data.health_endpoint
                }
            )
        elif data.type == "odata":
            connector = ODataConnector(
                connector_id=connector_id,
                name=data.name,
                config={
                    "base_url": data.base_url,
                    "service_root": data.service_root,
                    "auth_type": data.auth_type,
                    "token": data.token,
                    "username": data.username,
                    "password": data.password
                }
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Type non supporté: {data.type}. Types valides: postgres, mysql, mssql, rest, odata"
            )
        
        # Connecter
        await connector.connect()
        
        # Sauvegarder en base
        db_connector = Connector(
            id=connector_uuid,
            name=data.name,
            type=data.type,
            config=connector.config,
            status="active"
        )
        db.add(db_connector)
        db.commit()
        db.refresh(db_connector)
        
        # Ajouter en mémoire
        connectors[connector_id] = connector
        
        logger.info(f"Connecteur {data.type} créé: {connector_id}")
        
        return {
            "success": True,
            "connector_id": connector_id,
            "type": data.type,
            "db_uuid": str(connector_uuid),
            "saved_to_db": True
        }
        
    except ConnectorException as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/connectors")
async def list_connectors(db: Session = Depends(get_db)):
    db_connectors = db.query(Connector).all()
    
    return {
        "total": len(db_connectors),
        "in_memory": len(connectors),
        "connectors": [
            {
                "id": str(c.id),
                "name": c.name,
                "type": c.type,
                "status": c.status,
                "created_at": c.created_at.isoformat()
            }
            for c in db_connectors
        ]
    }


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


@app.post("/ask")
async def ask_question(request: AskRequest, db: Session = Depends(get_db)):
    """Pose une question en français, OnePilot génère le SQL et l'exécute."""
    
    if request.connector_id not in connectors:
        raise HTTPException(status_code=404, detail="Connecteur introuvable")
    
    try:
        from datetime import datetime
        
        connector = connectors[request.connector_id]
        schema = await connector.get_schema()
        
        start = datetime.now()
        sql = await llm_engine.generate_sql(request.question, schema)
        llm_time = (datetime.now() - start).total_seconds() * 1000
        
        start = datetime.now()
        results = await connector.execute_query(sql)
        query_time = (datetime.now() - start).total_seconds() * 1000
        
        conversation = Conversation(
            user_id="default_user",
            question=request.question,
            answer=json.dumps(results),
            sql_query=sql,
            confidence=0.8
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        logger.info(f"Conversation sauvegardée: {conversation.id}")
        
        return {
            "success": True,
            "conversation_id": str(conversation.id),
            "question": request.question,
            "sql": sql,
            "results": results,
            "count": len(results),
            "llm_time_ms": round(llm_time, 2),
            "query_time_ms": round(query_time, 2)
        }
        
    except LLMException as e:
        raise HTTPException(status_code=500, detail=f"Erreur LLM: {e.message}")
    except ConnectorException as e:
        raise HTTPException(status_code=500, detail=f"Erreur SQL: {e.message}")


@app.get("/history")
async def get_history(limit: int = 10, db: Session = Depends(get_db)):
    """Récupère les dernières conversations."""
    conversations_list = db.query(Conversation).order_by(
        Conversation.created_at.desc()
    ).limit(limit).all()
    
    return {
        "total": len(conversations_list),
        "conversations": [
            {
                "id": str(c.id),
                "question": c.question,
                "sql_query": c.sql_query,
                "created_at": c.created_at.isoformat()
            }
            for c in conversations_list
        ]
    }


# ── Endpoints Monitoring ────────────────────────────────────
@app.get("/monitoring/health")
async def get_health():
    """Retourne l'état de santé global du système."""
    return monitoring_service.get_health_status()


@app.get("/monitoring/metrics")
async def get_metrics():
    """Retourne les métriques de performance."""
    return monitoring_service.get_metrics()


@app.post("/monitoring/check")
async def manual_check():
    """Force un check manuel de tous les connecteurs."""
    results = await monitoring_service.check_all_connectors(connectors)
    return {
        "success": True,
        "message": "Check manuel effectué",
        "results": results
    }


@app.get("/monitoring/connectors/{connector_id}")
async def get_connector_health(connector_id: str):
    """Retourne l'état de santé d'un connecteur spécifique."""
    if connector_id not in connectors:
        raise HTTPException(status_code=404, detail="Connecteur introuvable")
    
    result = await monitoring_service.check_connector(connector_id, connectors[connector_id])
    return result