#!/bin/bash
# Script pour démarrer le serveur web FastAPI

echo "🚀 Démarrage du serveur FastAPI..."

# Activer l'environnement virtuel si disponible
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Démarrer le serveur avec uvicorn
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8001

