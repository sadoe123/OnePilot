from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class ConnectorType(Enum):
    SQL      = "sql"
    API_REST = "api_rest"
    FILE_CSV = "file_csv"
    ERP_SAP  = "erp_sap"


class ConnectorStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING   = "connecting"
    CONNECTED    = "connected"
    ERROR        = "error"


class BaseConnector(ABC):
    """Classe abstraite que tous les connecteurs doivent implémenter."""

    def __init__(self, connector_id: str, name: str,
                 connector_type: ConnectorType, config: Dict[str, Any]):
        self.connector_id = connector_id
        self.name = name
        self.connector_type = connector_type
        self.config = config
        self.status = ConnectorStatus.DISCONNECTED
        self.last_connected: Optional[datetime] = None

    @abstractmethod
    async def connect(self) -> bool:
        """Établit la connexion."""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Ferme la connexion."""
        pass

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Teste la connexion sans la maintenir."""
        pass

    @abstractmethod
    async def get_schema(self) -> Dict[str, Any]:
        """Récupère le schéma complet de la source."""
        pass

    @abstractmethod
    async def execute_query(self, query: str, params: Dict = None) -> List[Dict[str, Any]]:
        """Exécute une requête sur la source."""
        pass

    def get_status(self) -> Dict[str, Any]:
        """Retourne l'état actuel du connecteur."""
        return {
            "connector_id": self.connector_id,
            "name": self.name,
            "type": self.connector_type.value,
            "status": self.status.value,
            "last_connected": self.last_connected.isoformat() if self.last_connected else None
        }