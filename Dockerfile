# Utilisation de l'image Python slim pour un environnement léger
FROM python:3.12-slim

# Installation de uv (si nécessaire pour gérer les dépendances)
RUN pip install --no-cache-dir uv

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# # Copier les fichiers de configuration des dépendances
# COPY pyproject.toml uv.lock* ./

# # Synchroniser les dépendances sans installer le projet
# RUN uv sync --frozen --no-install-project

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le code source dans le conteneur
COPY . .

# Vérification que `adk` est bien installé
RUN adk --version

# Exposer le port 8000 pour l'application
EXPOSE 8000

# Commande par défaut pour exécuter l'application
CMD ["adk", "web", "--port=8080", "--host=0.0.0.0"]