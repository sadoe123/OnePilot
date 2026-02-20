import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from urllib.parse import urlencode

from ..base import BaseConnector, ConnectorType, ConnectorStatus
from ...core.exceptions import (
    ConnectionFailedException,
    QueryExecutionException,
    SchemaDiscoveryException
)

logger = logging.getLogger(__name__)


class ODataConnector(BaseConnector):
    """Connecteur pour APIs OData (SAP, Dynamics, SharePoint, etc.)."""

    def __init__(self, connector_id: str, name: str, config: Dict[str, Any]):
        super().__init__(
            connector_id=connector_id,
            name=name,
            connector_type=ConnectorType.API_REST,
            config=config
        )
        self.base_url = config.get("base_url")
        self.service_root = config.get("service_root", "")
        self._client: Optional[httpx.AsyncClient] = None

    def _get_auth_headers(self) -> Dict[str, str]:
        """Construit les en-têtes d'authentification."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        auth_type = self.config.get("auth_type", "basic")
        
        if auth_type == "bearer":
            token = self.config.get("token")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        
        return headers

    async def connect(self) -> bool:
        try:
            self.status = ConnectorStatus.CONNECTING
            full_url = f"{self.base_url}/{self.service_root}"
            logger.info(f"Connexion à OData: {full_url}")

            auth = None
            if self.config.get("auth_type") == "basic":
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

            # Test de connexion - récupérer le service document
            response = await self._client.get(f"{self.service_root}/$metadata")
            
            if response.status_code < 400:
                logger.info(f"Connecté: OData service (status {response.status_code})")
                self.status = ConnectorStatus.CONNECTED
                self.last_connected = datetime.now()
                return True
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

        except Exception as e:
            self.status = ConnectorStatus.ERROR
            raise ConnectionFailedException(
                f"Échec connexion OData: {str(e)}",
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
                    f"{self.service_root}/$metadata",
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
        """Découvre les EntitySets disponibles depuis le service OData."""
        if not self._client:
            raise SchemaDiscoveryException("Non connecté")
        
        try:
            # Récupérer le service document
            response = await self._client.get(self.service_root)
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            
            service_doc = response.json()
            
            # Parser les EntitySets
            entity_sets = []
            
            if "value" in service_doc:
                for item in service_doc["value"]:
                    entity_sets.append({
                        "name": item.get("name"),
                        "url": item.get("url"),
                        "kind": item.get("kind", "EntitySet")
                    })
            
            return {
                "connector_id": self.connector_id,
                "base_url": self.base_url,
                "service_root": self.service_root,
                "entity_sets": entity_sets,
                "discovered_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise SchemaDiscoveryException(f"Échec découverte schéma OData: {str(e)}")

    async def execute_query(self, query: str, params: Dict = None) -> List[Dict[str, Any]]:
        """
        Exécute une requête OData.
        
        Exemples de query:
        - "Users" → GET /Users
        - "Users?$filter=Name eq 'John'" → avec filtre
        - "Users?$select=Name,Email&$top=10" → projection et pagination
        """
        if not self._client:
            raise QueryExecutionException("Non connecté")
        
        try:
            # Construire l'URL complète
            if query.startswith("/"):
                path = f"{self.service_root}{query}"
            else:
                path = f"{self.service_root}/{query}"
            
            # Ajouter les paramètres OData si fournis
            if params:
                query_params = []
                
                if "filter" in params:
                    query_params.append(f"$filter={params['filter']}")
                if "select" in params:
                    query_params.append(f"$select={params['select']}")
                if "top" in params:
                    query_params.append(f"$top={params['top']}")
                if "skip" in params:
                    query_params.append(f"$skip={params['skip']}")
                if "orderby" in params:
                    query_params.append(f"$orderby={params['orderby']}")
                
                if query_params:
                    separator = "&" if "?" in path else "?"
                    path += separator + "&".join(query_params)
            
            # Exécuter la requête
            response = await self._client.get(path)
            
            if response.status_code >= 400:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            
            result = response.json()
            
            # OData retourne généralement {"value": [...]}
            if "value" in result:
                return result["value"]
            elif isinstance(result, list):
                return result
            elif isinstance(result, dict):
                return [result]
            else:
                return [{"result": result}]
                
        except Exception as e:
            raise QueryExecutionException(
                f"Échec requête OData: {str(e)}",
                details={"query": query}
            )