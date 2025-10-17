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

### Build et Run le Conteneur 
```bash
docker build -t hackathon-backend:latest .
docker run --rm -it -p 8080:8080 --env-file .env --name hackathon-backend hackathon-backend:latest
```

### Utiliser cette URL une fois le conteneur run
http://localhost:8080/

Endpoints disponibles :
🏠 Root : http://localhost:8000/
📚 Documentation Swagger : http://localhost:8000/docs
📖 ReDoc : http://localhost:8000/redoc
❤️ Health check : http://localhost:8000/api/health
💬 Chat : http://localhost:8000/api/chat (POST)
Lien Escalidraw (Lecture): https://excalidraw.com/#json=SRJi3R8ImnvpIUQoH1fH0,u0hn4NIN0WpW7zaRhdmj9Q

Lien Escalidraw (Ecriture): https://excalidraw.com/#room=1718709f725b98ea9b9b,2RJaF-Fgk_OcC9r61GT2Pg

Documentation ADK: https://google.github.io/adk-docs/

# Servers MCP

- Mermaid : https://github.com/hustcc/mcp-mermaid?tab=readme-ov-file

- Graph : https://github.com/antvis/mcp-server-chart

- Notion : https://developers.notion.com/docs/mcp

- GMAIL : https://github.com/Ayush-k-Shukla/gmail-mcp-server

- Email : https://github.com/Shy2593666979/mcp-server-email

- Drive : 

# Technos

- UV : package manager
- ADK : framework agentic
- Pydantic pour les classes avec BaseModel
- Firestore : BDD Mongo
- (Cloud SQL BDD User ?)
- OAuth Google ?
- Backend Django ?
