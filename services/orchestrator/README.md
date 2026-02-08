# Orchestrator Service

Multi-agent coordination service using LangGraph for NeuroSync AI.

## Responsibilities
- Route requests to appropriate agents
- Manage agent state and workflow
- Coordinate multi-agent interactions via LangGraph state graph
- Handle session lifecycle

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Detailed health check |
| GET | `/healthz` | Liveness probe |
| POST | `/v1/session/start` | Start a learning session |
| GET | `/v1/agents/status` | Status of all registered agents |

## Development

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8010
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEUROSYNC_REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `NEUROSYNC_MONGODB_URI` | `mongodb://localhost:27017/neurosync` | MongoDB connection |
| `NEUROSYNC_OPENAI_API_KEY` | — | OpenAI API key |
