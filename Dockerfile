FROM python:3.12-slim

# uv (si vous l’utilisez)
RUN pip install --no-cache-dir uv

WORKDIR /app

# Dépendances
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-install-project

# Code
COPY . .

EXPOSE 8000

# Dev: hot reload (à utiliser avec un volume monté)
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
