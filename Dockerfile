# Image RunPod Serverless pour runpod_handler.py — le scoring
# déterministe V9 du projet (scoring.py), plus l'écriture optionnelle
# des résultats sur GitHub (github_push.py). Volontairement minimale :
# scoring.py/keywords.py sont du Python pur, github_push.py n'a besoin
# que de `requests` pour l'API REST de GitHub. Pas de feedparser/
# beautifulsoup4 (utilisés par le scanner complet, jamais par ce
# handler) et surtout pas de llama-cpp-python/huggingface_hub (aucun
# LLM dans cette première étape — voir la note d'architecture dans
# runpod_handler.py).
FROM python:3.11-slim

WORKDIR /app

COPY requirements-runpod.txt .
RUN pip install --no-cache-dir -r requirements-runpod.txt

COPY scoring.py keywords.py github_push.py runpod_handler.py ./

CMD ["python", "-u", "runpod_handler.py"]
