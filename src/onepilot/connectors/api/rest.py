import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import json

from ..base import BaseConnector, ConnectorType, ConnectorStatus
from ...core.exceptions import (
    ConnectionFailedException,
    QueryExecutionException,
    SchemaDiscoveryException
)

logger = logging.getLogger(__name__)


class RESTConnector(BaseConnector):
    """Connecteur pour APIs REST génériques."""

    def __init__(self, connector_id: str, name: str, config: Dict[str, Any]):
        super().__init__(
            connector_id=connector_id,
            name=name,
            connector_type=ConnectorType.API_REST,
            config=config
        )
        self.base_url = config.get("base_url")
        self.headers = config.get("headers", {})
        self.auth_type = config.get("auth_type", "none")  # none, bearer, basic, api_key
        self._client: Optional[httpx.AsyncClient] = None

    def _get_auth_headers(self) -> Dict[str, str]:
        """Construit les en-têtes d'authentification."""
        headers = self.headers.copy()
        
        if self.auth_type == "bearer":
            token = self.config.get("token")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        
        elif self.auth_type == "api_key":
            key_name = self.config.get("api_key_name", "X-API-Key")
            api_key = self.config.get("api_key")
            if api_key:
                headers[key_name] = api_key
        
        elif self.auth_type == "basic":
            # httpx gère automatiquement basic auth avec auth=(user, pass)
            pass
        
        return headers

    async def connect(self) -> bool:
        try:
            self.status = ConnectorStatus.CONNECTING
            logger.info(f"Connexion à REST API: {self.base_url}")

            auth = None
            if self.auth_type == "basic":
                auth = httpx.BasicAuth(
                    self.config.get("username"),
                    self.config.get("password")
                )

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._get_auth_headers(),
                auth=auth,
                timeout=30.0,
                follow_redirects=True
            )

            # Test de connexion
            response = await self._client.get(self.config.get("health_endpoint", "/"))
            
            if response.status_code < 400:
                logger.info(f"Connecté: {self.base_url} (status {response.status_code})")
                self.status = ConnectorStatus.CONNECTED
                self.last_connected = datetime.now()
                return True
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

        except Exception as e:
            self.status = ConnectorStatus.ERROR
            raise ConnectionFailedException(
                f"Échec connexion REST API: {str(e)}",
                details={"base_url": self.base_url}
            )

    async def disconnect(self) -> bool:
        try:
            if self._client:
                await self._client.aclose()
                self._client = None
            self.status = ConnectorStatus.DISCONNECTED
            logger.info(f"Déconnecté: {self.name}")
            return True
        except Exception as e:
            logger.error(f"Erreur déconnexion: {str(e)}")
            return False

    async def test_connection(self) -> Dict[str, Any]:
        start = datetime.now()
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
                response = await client.get(
                    self.config.get("health_endpoint", "/"),
                    headers=self._get_auth_headers()
                )
                latency = (datetime.now() - start).total_seconds() * 1000
                
                return {
                    "success": response.status_code < 400,
                    "message": f"HTTP {response.status_code}",
                    "latency_ms": round(latency, 2)
                }
        except Exception as e:
            return {"success": False, "message": "Échec", "error": str(e)}

    async def get_schema(self) -> Dict[str, Any]:
        """Découvre les endpoints disponibles via OpenAPI/Swagger si disponible."""
        if not self._client:
            raise SchemaDiscoveryException("Non connecté")
        
        try:
            endpoints = []
            
            # Essayer de récupérer le schéma OpenAPI
            openapi_paths = ["/openapi.json", "/swagger.json", "/api-docs"]
            
            for path in openapi_paths:
                try:
                    response = await self._client.get(path)
                    if response.status_code == 200:
                        spec = response.json()
                        
                        # Parser les endpoints depuis OpenAPI
                        if "paths" in spec:
                            for path, methods in spec["paths"].items():
                                for method, details in methods.items():
                                    if method in ["get", "post", "put", "delete"]:
                                        endpoints.append({
                                            "path": path,
                                            "method": method.upper(),
                                            "description": details.get("summary", ""),
                                            "parameters": details.get("parameters", [])
                                        })
                        break
                except:
                    continue
            
            # Si pas de OpenAPI, retourner les endpoints configurés manuellement
            if not endpoints and "endpoints" in self.config:
                endpoints = self.config["endpoints"]
            
            return {
                "connector_id": self.connector_id,
                "base_url": self.base_url,
                "endpoints": endpoints,
                "discovered_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise SchemaDiscoveryException(f"Échec découverte schéma: {str(e)}")

    async def execute_query(self, query: str, params: Dict = None) -> List[Dict[str, Any]]:
        """
        Exécute une requête HTTP.
        query format: "GET /users" ou "POST /users" avec params
        """
        if not self._client:
            raise QueryExecutionException("Non connecté")
        
        try:
            # Parser la query
            parts = query.strip().split(maxsplit=1)
            method = parts[0].upper()
            path = parts[1] if len(parts) > 1 else "/"
            
            # Préparer les paramètres
            request_params = params or {}
            
            # Exécuter la requête
            if method == "GET":
                response = await self._client.get(path, params=request_params.get("params"))
            elif method == "POST":
                response = await self._client.post(path, json=request_params.get("json"))
            elif method == "PUT":
                response = await self._client.put(path, json=request_params.get("json"))
            elif method == "DELETE":
                response = await self._client.delete(path)
            else:
                raise QueryExecutionException(f"Méthode HTTP non supportée: {method}")
            
            # Parser la réponse
            if response.status_code >= 400:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            
            result = response.json()
            
            # Normaliser en liste de dicts
            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                return [result]
            else:
                return [{"result": result}]
                
        except Exception as e:
            raise QueryExecutionException(
                f"Échec requête REST: {str(e)}",
                details={"query": query}
            )