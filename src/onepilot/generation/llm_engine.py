import httpx
import json
from typing import Dict, Any, Optional
import logging

from ..core.config import settings
from ..core.exceptions import LLMException

logger = logging.getLogger(__name__)


class LLMEngine:
    """Moteur LLM pour générer du SQL depuis du langage naturel."""

    def __init__(self):
        self.base_url = settings.ollama_host
        self.model = settings.ollama_model

    async def generate_sql(
        self,
        question: str,
        schema: Dict[str, Any]
    ) -> str:
        """
        Génère une requête SQL à partir d'une question en français.
        
        Args:
            question: Question en langage naturel
            schema: Schéma des tables disponibles
            
        Returns:
            Requête SQL générée
        """
        # Construction du prompt avec le schéma
        prompt = self._build_prompt(question, schema)
        
        logger.info(f"Question: {question}")
        logger.debug(f"Prompt envoyé au LLM: {prompt[:200]}...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,  # Peu créatif, plus précis
                            "top_p": 0.9
                        }
                    }
                )
                
                if response.status_code != 200:
                    raise LLMException(f"Ollama error: {response.text}")
                
                result = response.json()
                sql = self._extract_sql(result["response"])
                
                logger.info(f"SQL généré: {sql}")
                return sql
                
        except httpx.TimeoutException:
            raise LLMException("Timeout lors de l'appel à Ollama")
        except Exception as e:
            raise LLMException(f"Erreur LLM: {str(e)}")

    def _build_prompt(self, question: str, schema: Dict[str, Any]) -> str:
        """Construit le prompt pour le LLM."""
        
        # Formatage du schéma
        tables_info = []
        for table in schema.get("tables", []):
            cols = ", ".join([
                f"{c['name']} ({c['type']})" 
                for c in table["columns"]
            ])
            tables_info.append(f"- {table['name']}: {cols}")
        
        schema_text = "\n".join(tables_info)
        
        prompt = f"""Tu es un expert SQL PostgreSQL. Ta mission est de générer UNIQUEMENT du SQL valide.

SCHÉMA DE LA BASE DE DONNÉES:
{schema_text}

RÈGLES IMPORTANTES:
1. Génère UNIQUEMENT la requête SQL, rien d'autre
2. Pas de markdown, pas de ```sql```, juste le SQL pur
3. Utilise PostgreSQL syntax
4. Sois précis et efficace
5. Si la question ne peut pas être résolue, retourne: SELECT 'Impossible de répondre' as error

QUESTION: {question}

SQL:"""
        
        return prompt

    def _extract_sql(self, llm_response: str) -> str:
        """Extrait le SQL pur de la réponse du LLM."""
        
        # Nettoyer la réponse
        sql = llm_response.strip()
        
        # Retirer les markdown code blocks si présents
        if "```sql" in sql:
            sql = sql.split("```sql")[1].split("```")[0].strip()
        elif "```" in sql:
            sql = sql.split("```")[1].split("```")[0].strip()
        
        # Retirer les commentaires de début
        lines = sql.split("\n")
        sql_lines = [l for l in lines if not l.strip().startswith("--")]
        sql = "\n".join(sql_lines).strip()
        
        # S'assurer qu'il se termine par ;
        if not sql.endswith(";"):
            sql += ";"
        
        return sql


# Instance globale
llm_engine = LLMEngine()