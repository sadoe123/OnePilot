# OnePilot 🚀

Agent IA conversationnel universel pour ERP - Version 1.0

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Description

**OnePilot** est un agent IA conversationnel de nouvelle génération capable de se connecter à **n'importe quel ERP** (SAP, Microsoft Dynamics, SAGE, Oracle, etc.) et de répondre à vos questions métier en temps réel.

### ✨ Fonctionnalités principales

- 🔌 **Connectivité universelle** : SQL, API REST/SOAP, OData, GraphQL, fichiers
- 🧠 **Intelligence sémantique** : Détection automatique des relations entre données
- 💬 **Multimodal** : Interface texte, vocale (STT/TTS) et dashboards interactifs
- 📊 **Génération de dashboards** : Visualisations type PowerBI créées automatiquement
- 🔒 **100% On-premise** : Vos données restent chez vous
- 📚 **Apprentissage continu** : S'améliore avec le feedback utilisateur

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Interfaces Utilisateur          │
│   Chat Web  │  Voix  │  Admin Panel    │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│        Apprentissage Continu            │
│   Feedback  │  RAG  │  Validation      │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│       Génération de Réponses            │
│   LLM  │  Dashboards  │  TTS           │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│              NLU & Planning             │
│   Intent  │  STT  │  Query Planner     │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│      Intelligence Métadonnées           │
│   Relations  │  Embeddings  │  Profiler│
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│         Accès Universel Données         │
│   SQL  │  APIs  │  ERPs  │  Fichiers   │
└─────────────────────────────────────────┘
```

---

## 🚀 Installation rapide

### Prérequis

- Python 3.11+
- Docker & Docker Compose
- Git
- Poetry (gestionnaire de dépendances Python)

### Étape 1 : Cloner le projet

```bash
git clone https://github.com/votre-org/onepilot.git
cd onepilot
```

### Étape 2 : Configuration

```bash
# Copier le fichier d'environnement
cp .env.example .env

# Éditer .env avec vos valeurs
notepad .env  # Windows
nano .env     # Linux/Mac
```

### Étape 3 : Démarrer les services Docker

```bash
# Démarrer PostgreSQL, Redis et Ollama
docker-compose up -d

# Vérifier que tout fonctionne
docker-compose ps
```

### Étape 4 : Télécharger un modèle LLM

```bash
# Télécharger Llama2 (7B, ~4GB)
docker exec -it onepilot-ollama ollama pull llama2

# Ou Mistral (7B, plus performant en français)
docker exec -it onepilot-ollama ollama pull mistral

# Tester le modèle
docker exec -it onepilot-ollama ollama run llama2 "Bonjour"
```

### Étape 5 : Installer les dépendances Python

```bash
# Installer Poetry si nécessaire
pip install poetry

# Installer les dépendances du projet
poetry install

# Activer l'environnement virtuel
poetry shell
```

### Étape 6 : Initialiser la base de données

```bash
# Créer les tables
poetry run alembic upgrade head
```

### Étape 7 : Lancer l'application

```bash
# Démarrer le serveur FastAPI
poetry run uvicorn src.onepilot.api.main:app --reload

# L'API est maintenant accessible sur http://localhost:8000
# Documentation interactive : http://localhost:8000/docs
```

---

## 📖 Documentation

- [Guide de démarrage complet](docs/getting_started.md)
- [Architecture détaillée](docs/architecture.md)
- [API Reference](docs/api_reference.md)
- [Guide de déploiement](docs/deployment.md)
- [Contributing](docs/contributing.md)

---

## 🧪 Tests

```bash
# Lancer tous les tests
poetry run pytest

# Tests avec couverture
poetry run pytest --cov=src/onepilot --cov-report=html

# Tests d'un module spécifique
poetry run pytest tests/unit/test_connectors.py
```

---

## 🔧 Utilisation de base

### 1. Créer un connecteur

```bash
curl -X POST "http://localhost:8000/connectors/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ma base de production",
    "host": "localhost",
    "port": 5432,
    "database": "erp_prod",
    "user": "admin",
    "password": "secret"
  }'
```

### 2. Poser une question

```bash
curl -X POST "http://localhost:8000/chat/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Combien de commandes avons-nous ce mois-ci ?"
  }'
```

### 3. Générer un dashboard

```bash
curl -X POST "http://localhost:8000/dashboard/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Affiche-moi l'\''évolution du CA par mois"
  }'
```

---

## 📊 Stack Technique

### Backend
- **Framework** : FastAPI
- **Base de données** : PostgreSQL
- **Cache** : Redis
- **ORM** : SQLAlchemy
- **LLM** : Ollama (Llama2, Mistral, etc.)

### NLP & ML
- **NLU** : spaCy
- **Embeddings** : Sentence Transformers
- **Vector Store** : ChromaDB
- **STT** : OpenAI Whisper
- **TTS** : Coqui TTS

### Frontend
- **Framework** : React + TypeScript
- **Build** : Vite
- **UI** : Tailwind CSS
- **Visualisation** : Plotly.js

### DevOps
- **Containerisation** : Docker
- **Orchestration** : Docker Compose / Kubernetes
- **CI/CD** : GitHub Actions
- **Monitoring** : Prometheus + Grafana

---

## 🗺️ Roadmap

### ✅ Phase 1 - MVP (Terminé)
- [x] Connecteur PostgreSQL
- [x] API FastAPI de base
- [x] LLM pour génération SQL
- [x] Interface chat simple

### 🚧 Phase 2 - En cours
- [ ] Support multi-bases SQL (MySQL, MSSQL, Oracle)
- [ ] Connecteurs API REST
- [ ] Interface vocale (STT/TTS)
- [ ] Génération de dashboards

### 📅 Phase 3 - Planifié
- [ ] Détection automatique de relations
- [ ] Système RAG pour apprentissage
- [ ] Support SAP, Dynamics
- [ ] Frontend React complet

### 🔮 Phase 4 - Futur
- [ ] Support multi-tenant
- [ ] App mobile
- [ ] Marketplace de connecteurs
- [ ] ML avancé (prédictions, anomalies)

---

## 🤝 Contribution

Les contributions sont les bienvenues ! Consultez [CONTRIBUTING.md](CONTRIBUTING.md) pour les guidelines.

### Comment contribuer

1. Fork le projet
2. Créez une branche (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

---

## 📝 License

Ce projet est sous licence MIT. Voir [LICENSE](LICENSE) pour plus de détails.

---

## 👥 Auteurs

- **Ghassen Riahi** - *Créateur du projet* - [@ghassen](https://github.com/ghassen)

---

## 🙏 Remerciements

- OpenAI pour Whisper
- Meta pour Llama2
- Mistral AI pour Mistral
- La communauté open source

---

## 📞 Support

- 📧 Email : support@onepilot.ai
- 💬 Discord : [OnePilot Community](https://discord.gg/onepilot)
- 📚 Documentation : [docs.onepilot.ai](https://docs.onepilot.ai)
- 🐛 Issues : [GitHub Issues](https://github.com/votre-org/onepilot/issues)

---

## ⭐ Star History

Si ce projet vous aide, n'hésitez pas à mettre une ⭐ !

---

**Made with ❤️ by the OnePilot Team**
