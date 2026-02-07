# Getting Started

## Prerequisites

- Python 3.11+
- Node.js 18+
- Ollama (for local LLM inference)
- ChromaDB (optional, for learning system)

## Installation

```bash
git clone https://github.com/lalphadb/ai-orchestrator.git
cd ai-orchestrator

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Frontend
cd ../frontend
npm install
```

## Configuration

Edit `backend/.env`:

```env
SECRET_KEY=<generate with: python3 -c "import secrets; print(secrets.token_hex(32))">
DATABASE_URL=sqlite:///./data/orchestrator.db
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b
```

## Running

```bash
# Terminal 1 - Backend
cd backend
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8001

# Terminal 2 - Frontend
cd frontend
npm run dev
```

- Backend API: http://localhost:8001/health
- Frontend: http://localhost:5173

## Verify

```bash
# Backend health
curl http://localhost:8001/health

# Run tests
cd backend && ../.venv/bin/python -m pytest tests/ -x -q
cd frontend && npx vitest run
```

## Ports

| Service | Port |
|---------|------|
| Backend API | 8001 |
| Frontend Dev | 5173 |
| Ollama | 11434 |
| ChromaDB | 8000 |

## Troubleshooting

**Backend won't start** - Check `pip install -r requirements.txt` completed without errors.

**Frontend won't start** - Run `rm -rf node_modules && npm install`.

**WebSocket disconnected** - Verify backend is running and JWT token is valid.

**No LLM response** - Check `ollama list` shows available models.
