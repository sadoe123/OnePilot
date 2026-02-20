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

