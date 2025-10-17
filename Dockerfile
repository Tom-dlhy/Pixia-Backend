# ...existing code...
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# installer uv avant, mettre à jour pip
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir uv

# Copier requirements d'abord pour utiliser le cache Docker
COPY requirements.txt ./ 
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code
COPY . .

# Vérifier adk (si l'exécutable est disponible après l'installation)
RUN adk --version || true

# Exposer le port sur lequel le container écoute (aligné avec CMD)
EXPOSE 8080

# WORKDIR /app/src/agents
CMD ["uv", "run","dev", "--port=8080", "--host=0.0.0.0"]

# ...existing code...