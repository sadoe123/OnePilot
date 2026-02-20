import asyncio
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MonitoringService:
    """Service de monitoring pour les connecteurs."""
    
    def __init__(self):
        self.health_checks: Dict[str, Dict[str, Any]] = {}
        self.check_interval = 300  # 5 minutes
        self.is_running = False
        self._task = None
    
    async def start(self, connectors: Dict):
        """Démarre le monitoring automatique."""
        if self.is_running:
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._monitor_loop(connectors))
        logger.info("Monitoring service started")
    
    async def stop(self):
        """Arrête le monitoring."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Monitoring service stopped")
    
    async def _monitor_loop(self, connectors: Dict):
        """Boucle de monitoring."""
        while self.is_running:
            try:
                await self.check_all_connectors(connectors)
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erreur dans la boucle de monitoring: {e}")
                await asyncio.sleep(60)  # Attendre 1 minute en cas d'erreur
    
    async def check_all_connectors(self, connectors: Dict) -> Dict[str, Any]:
        """Vérifie l'état de tous les connecteurs."""
        results = {}
        
        for connector_id, connector in connectors.items():
            try:
                check_result = await self.check_connector(connector_id, connector)
                results[connector_id] = check_result
            except Exception as e:
                results[connector_id] = {
                    "status": "error",
                    "error": str(e),
                    "checked_at": datetime.now().isoformat()
                }
        
        self.health_checks = results
        return results
    
    async def check_connector(self, connector_id: str, connector) -> Dict[str, Any]:
        """Vérifie l'état d'un connecteur spécifique."""
        start = datetime.now()
        
        try:
            # Test de connexion
            test_result = await connector.test_connection()
            
            latency = (datetime.now() - start).total_seconds() * 1000
            
            return {
                "connector_id": connector_id,
                "name": connector.name,
                "type": connector.connector_type.value,
                "status": "healthy" if test_result.get("success") else "unhealthy",
                "latency_ms": round(latency, 2),
                "last_connected": connector.last_connected.isoformat() if connector.last_connected else None,
                "checked_at": datetime.now().isoformat(),
                "details": test_result
            }
        except Exception as e:
            return {
                "connector_id": connector_id,
                "name": connector.name,
                "type": connector.connector_type.value,
                "status": "error",
                "error": str(e),
                "checked_at": datetime.now().isoformat()
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Retourne l'état de santé global."""
        if not self.health_checks:
            return {
                "status": "unknown",
                "message": "Aucun check effectué",
                "connectors": {}
            }
        
        total = len(self.health_checks)
        healthy = sum(1 for c in self.health_checks.values() if c.get("status") == "healthy")
        unhealthy = sum(1 for c in self.health_checks.values() if c.get("status") == "unhealthy")
        errors = sum(1 for c in self.health_checks.values() if c.get("status") == "error")
        
        overall_status = "healthy"
        if errors > 0:
            overall_status = "critical"
        elif unhealthy > 0:
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "total_connectors": total,
            "healthy": healthy,
            "unhealthy": unhealthy,
            "errors": errors,
            "last_check": max(
                (c.get("checked_at") for c in self.health_checks.values()),
                default=None
            ),
            "connectors": self.health_checks
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques de performance."""
        if not self.health_checks:
            return {"message": "Aucune donnée disponible"}
        
        latencies = [
            c.get("latency_ms", 0) 
            for c in self.health_checks.values() 
            if c.get("latency_ms")
        ]
        
        return {
            "total_connectors": len(self.health_checks),
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
            "min_latency_ms": min(latencies) if latencies else 0,
            "max_latency_ms": max(latencies) if latencies else 0,
            "uptime_percentage": round(
                (sum(1 for c in self.health_checks.values() if c.get("status") == "healthy") / 
                 len(self.health_checks) * 100), 2
            ) if self.health_checks else 0
        }


# Instance globale
monitoring_service = MonitoringService()