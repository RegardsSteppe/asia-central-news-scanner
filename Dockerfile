# Image RunPod Serverless pour rp_handler.py — le scoring
# déterministe V9 du projet (scoring.py), plus l'écriture optionnelle
# des résultats sur GitHub (github_push.py). Volontairement minimale :
# scoring.py/keywords.py sont du Python pur, github_push.py n'a besoin
# que de `requests` pour l'API REST de GitHub. Pas de feedparser/
# beautifulsoup4 (utilisés par le scanner complet, jamais par ce
# handler) et surtout pas de llama-cpp-python/huggingface_hub (aucun
# LLM dans cette première étape — voir la note d'architecture dans
# rp_handler.py).
FROM python:3.11-slim

WORKDIR /app

COPY requirements-runpod.txt .
RUN pip install --no-cache-dir -r requirements-runpod.txt

# Doit couvrir toute la fermeture transitive des imports de
# rp_handler.py, sinon l'endpoint plante au démarrage. Vérifié par
# tests/test_runpod_image.py : scoring.py a gagné une dépendance
# (matching.py) lors d'un refactor et l'image est restée cassée sans
# que rien ne le signale.
COPY scoring.py keywords.py matching.py github_push.py rp_handler.py ./

CMD ["python", "-u", "rp_handler.py"]
