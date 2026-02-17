class OnePilotException(Exception):
    """Exception de base pour tout OnePilot."""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ConnectorException(OnePilotException):
    """Problème avec un connecteur de données."""
    pass


class ConnectionFailedException(ConnectorException):
    """Échec de connexion à une source de données."""
    pass


class QueryExecutionException(ConnectorException):
    """Échec lors de l'exécution d'une requête."""
    pass


class SchemaDiscoveryException(ConnectorException):
    """Échec lors de la découverte du schéma."""
    pass


class LLMException(OnePilotException):
    """Erreur lors de l'interaction avec le LLM."""
    pass


class ConfigurationException(OnePilotException):
    """Configuration invalide ou manquante."""
    pass