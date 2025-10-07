# Hackathon

Attention pour l'install vous allez peut-être devoir augmenter la env var


```bash
export UV_HTTP_TIMEOUT=120
```

pck google-adk est lourd

### Comment setup 

```bash
git clone https----lerepo
cd le repo
uv sync
```

### Lancer le serveur de dev en local 

```bash
uv run dev
```

Endpoints disponibles :
🏠 Root : http://localhost:8000/
📚 Documentation Swagger : http://localhost:8000/docs
📖 ReDoc : http://localhost:8000/redoc
❤️ Health check : http://localhost:8000/api/health
💬 Chat : http://localhost:8000/api/chat (POST)