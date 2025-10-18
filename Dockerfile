FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Mettre à jour pip
RUN pip install --no-cache-dir --upgrade pip

# Copier les fichiers de dépendances d'abord pour tirer parti du cache Docker
COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste de l'application
COPY . .

# Port exposé (par défaut 8080)
EXPOSE 8080


# Lancer l'app avec uvicorn directement sur le module FastAPI
# Utilise le chemin module:variable défini dans src/app/main.py
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8080"]