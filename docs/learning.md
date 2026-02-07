# Learning System

ChromaDB-powered memory system that enables the platform to improve over time.

## Collections

| Collection | Content |
|------------|---------|
| `ai_experiences` | Full interaction history with embeddings |
| `ai_patterns` | Successful tool sequences and strategies |
| `ai_corrections` | Error recovery strategies |
| `ai_user_context` | User preferences and working styles |

## How It Works

1. **Retrieval** - Before execution, search ChromaDB for similar past queries
2. **Execution** - Apply known patterns, avoid known failures
3. **Storage** - Store interaction with embedding after execution
4. **Feedback** - User ratings improve pattern scoring

## Configuration

```env
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_EMBEDDING_MODEL=bge-m3
LEARNING_TOP_K=3
LEARNING_SIMILARITY_THRESHOLD=0.7
LEARNING_ENABLED=true
```

## ChromaDB Setup

```bash
docker run -d -p 8000:8000 chromadb/chroma:latest

# Verify
curl http://localhost:8000/api/v1/heartbeat
```

## API Endpoints

- `POST /api/v1/learning/feedback` - Submit rating and comment
- `GET /api/v1/learning/feedback` - List feedback entries
- `GET /api/v1/learning/similar?query=...` - Find similar past interactions
