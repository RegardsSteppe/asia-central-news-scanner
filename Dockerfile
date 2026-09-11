# Image RunPod Serverless pour runpod_handler.py — le scoring
# déterministe V9 du projet (scoring.py), rien d'autre. Volontairement
# minimale : seul scoring.py dépend de keywords.py (Python pur, aucune
# dépendance réseau/HTML), donc l'image n'a besoin que du runtime
# RunPod. Pas de feedparser/requests/beautifulsoup4 (utilisés par le
# scanner complet, jamais par ce handler) et surtout pas de
# llama-cpp-python/huggingface_hub (aucun LLM dans cette première
# étape — voir la note d'architecture dans runpod_handler.py).
FROM python:3.11-slim

WORKDIR /app

COPY requirements-runpod.txt .
RUN pip install --no-cache-dir -r requirements-runpod.txt

COPY scoring.py keywords.py runpod_handler.py ./

CMD ["python", "-u", "runpod_handler.py"]
