# Learning System Overview

AI Orchestrator includes a feedback-driven learning system that enables the platform to improve over time by storing and retrieving successful patterns, failed attempts, and user preferences.

## Overview

The learning system uses ChromaDB, a vector database optimized for similarity search, to store:

- **Conversation history** - Full context of user interactions and AI responses
- **User feedback** - Thumbs up/down ratings and optional comments
- **Successful patterns** - Tool sequences and strategies that worked
- **Error corrections** - Failed attempts and their successful resolutions
- **User preferences** - Individual working styles and preferred approaches

**Key Benefit:** The system becomes faster, more accurate, and more personalized with each interaction.

---

## How It Works

### Learning Cycle

```
┌─────────────────────────────────────────────────────────┐
│                   USER REQUEST                          │
│             "Deploy my app with Docker"                 │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│         1. RETRIEVAL (Before Execution)                 │
│                                                         │
│  - Search ChromaDB for similar past queries            │
│  - Retrieve successful tool sequences                  │
│  - Load known error corrections                        │
│  - Apply user preferences                              │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│         2. EXECUTION (With Context)                     │
│                                                         │
│  - Execute with knowledge from past experiences        │
│  - Avoid known failure patterns                        │
│  - Try successful approaches first                     │
│  - Test and memorize new strategies                    │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│         3. STORAGE (After Execution)                    │
│                                                         │
│  - Store complete interaction with embedding           │
│  - Record tools used and their results                 │
│  - Save execution duration and iteration count         │
│  - Wait for user feedback                              │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│         4. FEEDBACK (User Rating)                       │
│                                                         │
│  👍 Positive → Increases pattern score (+1)            │
│  👎 Negative → Decreases pattern score (-1)            │
│  💬 Comment → Adds context for future improvements     │
└─────────────────────────────────────────────────────────┘
```

---

## ChromaDB Integration

### Collections

The learning system organizes data into specialized ChromaDB collections:

#### 1. Experiences Collection (`ai_experiences`)
Stores complete interaction history with semantic embeddings.

**Contents:**
- User query (text + embedding)
- AI response
- Tools used and their sequence
- Execution duration
- Iteration count
- Success/failure status
- Timestamp

**Usage:** Retrieved via vector similarity search to find relevant past solutions.

#### 2. Patterns Collection (`ai_patterns`)
Stores successful tool sequences and strategies.

**Contents:**
- Pattern description
- Tool sequence (ordered list)
- Success rate
- Average execution time
- Context where it applies
- Number of times used

**Usage:** Applied automatically when similar patterns are detected.

#### 3. Corrections Collection (`ai_corrections`)
Stores error recovery strategies.

**Contents:**
- Error type and message
- Failed approach
- Successful solution
- Tools used in recovery
- Applicable context

**Usage:** Auto-recovery system uses these to fix known errors without LLM intervention.

#### 4. User Context Collection (`ai_user_context`)
Stores user-specific preferences and working styles.

**Contents:**
- Preferred tools
- Coding style preferences
- Response format preferences
- Common task types
- Working patterns

**Usage:** Personalizes responses based on individual user behavior.

---

### Embedding Model

**Default:** `bge-m3` (BAAI General Embedding, Multilingual)
- Dimensions: 1024
- Languages: 100+
- Best for: General-purpose text embedding

**Alternative:** `qwen3-embedding:8b` (Alibaba Qwen3)
- Dimensions: 4096
- Best for: Code and technical documentation
- Higher accuracy for programming tasks

**Configuration:**
```python
# backend/.env
CHROMA_EMBEDDING_MODEL=bge-m3
# or
CHROMA_EMBEDDING_MODEL=qwen3-embedding:8b
```

---

## Learning Strategies

### 1. Learning by Experience

The system remembers what worked and applies it to similar situations.

**Example:**

**First Time:**
```
User: "List files in /var/log"

Orchestrator:
  - Try list_directory("/var/log")     → Works!
  - Duration: 8 seconds
  - Iterations: 3
  - Store experience with embedding

Stored:
  query_embedding: [0.234, -0.567, ...]
  tools_used: ["list_directory"]
  success: true
```

**Second Time:**
```
User: "Show files in /tmp/logs"

Orchestrator:
  - Search ChromaDB for similar queries
  - Find: "List files in /var/log" (similarity: 0.89)
  - Apply known pattern: list_directory()
  - Duration: 2 seconds ⚡ (4x faster!)
  - Iterations: 1
```

**Result:** 75% faster execution by reusing learned patterns.

---

### 2. Learning by Patterns

The system detects recurring successful sequences and applies them automatically.

**Pattern Detection Example:**

```python
# Observed pattern after 10 deployments:
Pattern: "Docker Deployment"
Sequence:
  1. read_file("docker-compose.yml")      # Check config
  2. execute_command("docker-compose up -d")  # Deploy
  3. http_request("http://localhost:8080/health")  # Verify

Success Rate: 95%
Avg Duration: 5 seconds
```

**Next Time:**
```
User: "Deploy my Docker application"

Orchestrator:
  - Detect "Docker deployment" pattern
  - Apply known 3-step sequence
  - Skip exploration phase
  - Direct execution → Success!
```

**Common Patterns Learned:**
- Error recovery sequences (try X, if fails try Y)
- Testing workflows (build → test → deploy)
- Code quality checks (lint → format → typecheck)
- Debugging strategies (check logs → analyze → fix)

---

### 3. Learning by Errors

Every error becomes a lesson for automatic recovery.

**Error Learning Example:**

**First Occurrence:**
```
Command: execute_command("npm install")
Error: ModuleNotFoundError: No module named 'pytest'

Recovery Attempt:
  1. execute_command("pip install pytest")
  2. execute_command("npm install")  # Retry
  Success: ✅

Store Correction:
  error_pattern: "ModuleNotFoundError.*pytest"
  solution: "pip install pytest"
  context: "Python testing"
```

**Next Time:**
```
Command: execute_command("pytest tests/")
Error: ModuleNotFoundError: No module named 'pytest'

Orchestrator:
  - Search corrections collection
  - Find known solution
  - Auto-apply: pip install pytest
  - Retry original command
  - Success! (no LLM retry needed)
```

**Result:** 83% reduction in repeated errors, instant recovery.

---

### 4. Learning User Preferences

The system adapts to individual working styles over time.

**Preference Learning Example:**

**After 50 Interactions:**
```python
User Profile (lalpha):
{
  "preferred_tools": ["git", "docker", "pytest"],  # Most used
  "response_style": "concise",                     # Short answers preferred
  "code_style": "well-commented",                  # Code preferences
  "typical_tasks": [                               # Common workflows
    "deploy applications",
    "fix bugs",
    "write tests"
  ],
  "working_hours": "09:00-18:00",                  # Active hours
  "feedback_patterns": {
    "thumbs_up": ["quick fixes", "detailed examples"],
    "thumbs_down": ["lengthy explanations", "over-engineering"]
  }
}
```

**Adaptation:**
- Suggests Git commands proactively
- Provides concise responses with code examples
- Prioritizes testing in workflows
- Avoids verbose explanations

---

## Performance Improvements

### Typical Evolution

| Metric | Week 1 | Week 2 | Month 1 | Month 3 |
|--------|--------|--------|---------|---------|
| **Response Time** | 8s | 5s | 3s | 2s |
| **Success Rate** | 75% | 85% | 92% | 96% |
| **Iterations/Task** | 5 | 4 | 3 | 2 |
| **Repeated Errors** | 30/week | 15/week | 8/week | 5/week |
| **Pattern Reuse** | 0% | 25% | 60% | 80% |

**Overall Improvement After 3 Months:**
- 75% faster responses
- 28% higher success rate
- 60% fewer iterations
- 83% fewer repeated errors

---

## API Endpoints

### Submit Feedback

```http
POST /api/v1/learning/feedback
Content-Type: application/json
Authorization: Bearer <token>

{
  "conversation_id": "conv_123",
  "message_id": "msg_456",
  "rating": 1,  // 1 = thumbs up, -1 = thumbs down
  "comment": "Great solution, very fast!" // Optional
}
```

**Response:**
```json
{
  "success": true,
  "feedback_id": "fb_789",
  "updated_score": 5
}
```

---

### List Feedback

```http
GET /api/v1/learning/feedback?limit=20
Authorization: Bearer <token>
```

**Response:**
```json
{
  "feedback": [
    {
      "id": "fb_789",
      "conversation_id": "conv_123",
      "message_id": "msg_456",
      "rating": 1,
      "comment": "Great solution, very fast!",
      "timestamp": "2026-01-28T15:30:00Z"
    }
  ],
  "total": 150,
  "avg_rating": 0.85
}
```

---

### Find Similar Conversations

```http
GET /api/v1/learning/similar?query=deploy+docker+app&limit=5
Authorization: Bearer <token>
```

**Response:**
```json
{
  "similar": [
    {
      "id": "exp_123",
      "query": "Deploy my Docker application",
      "similarity": 0.92,
      "tools_used": ["read_file", "execute_command", "http_request"],
      "success": true,
      "duration_ms": 3200
    }
  ],
  "count": 5
}
```

---

## Configuration

### Environment Variables

```bash
# backend/.env

# ChromaDB Connection
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Collections
CHROMA_COLLECTION_EXPERIENCES=ai_experiences
CHROMA_COLLECTION_PATTERNS=ai_patterns
CHROMA_COLLECTION_CORRECTIONS=ai_corrections
CHROMA_COLLECTION_USER_CONTEXT=ai_user_context

# Embedding Model
CHROMA_EMBEDDING_MODEL=bge-m3
# Alternative for code: qwen3-embedding:8b

# Retrieval Settings
LEARNING_TOP_K=3           # Number of similar experiences to retrieve
LEARNING_SIMILARITY_THRESHOLD=0.7  # Minimum similarity score
LEARNING_ENABLED=true      # Enable/disable learning system
```

---

### Docker Compose

ChromaDB runs as a separate service:

```yaml
# docker-compose.yml

services:
  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"
    volumes:
      - chromadb_data:/chroma/chroma
    environment:
      - IS_PERSISTENT=TRUE
      - ANONYMIZED_TELEMETRY=FALSE

volumes:
  chromadb_data:
```

**Start ChromaDB:**
```bash
docker-compose up -d chromadb
```

**Verify:**
```bash
curl http://localhost:8000/api/v1/heartbeat
# {"nanosecond heartbeat": 1234567890}
```

---

## System Health Metrics

### Learning Memory Stats

```http
GET /api/v1/system/health
```

**Response includes:**
```json
{
  "learning_memory": {
    "experiences_count": 1247,      // Total experiences stored
    "patterns_count": 89,            // Detected patterns
    "corrections_count": 156,        // Error corrections
    "success_rate": 94.2,           // Overall success rate
    "avg_iterations": 2.3,           // Average iterations per task
    "feedback_count": 892,           // User feedback received
    "avg_feedback_score": 0.85       // Average rating
  }
}
```

---

### Prometheus Metrics

```promql
# Experience reuse rate
ai_orchestrator_learning_experiences_total{reused="true"}

# Pattern application success
ai_orchestrator_learning_patterns_applied_total{success="true"}

# Auto-corrections applied
ai_orchestrator_learning_corrections_applied_total

# Average feedback score
ai_orchestrator_evaluation_score_avg
```

---

## Usage Examples

### Example 1: First vs Repeat Execution

**First Deployment:**
```
User: "Deploy my app with Docker"

Orchestrator:
  ⏱️  Duration: 12 seconds
  🔄 Iterations: 5
  🔧 Tools: [read_file, execute_command, execute_command, http_request, git_status]
  ✅ Success
  💾 Stored as experience

Learning:
  - Saved query embedding
  - Stored tool sequence
  - Recorded duration
  - Created "Docker deployment" pattern
```

**Tenth Deployment:**
```
User: "Deploy my Docker application"

Orchestrator:
  🧠 Retrieved similar experience (similarity: 0.94)
  🎯 Applied known pattern: "Docker deployment"
  ⏱️  Duration: 3 seconds (4x faster!)
  🔄 Iterations: 2
  🔧 Tools: [read_file, execute_command, http_request]
  ✅ Success
```

---

### Example 2: Error Recovery Learning

**First Error:**
```
Command: pytest tests/
Error: ModuleNotFoundError: No module named 'pytest'

Orchestrator:
  💾 Stored error pattern
  🔧 Tried: pip install pytest
  ✅ Success
  💾 Stored correction

Total Time: 15 seconds (8s error + 7s recovery)
```

**Next Time:**
```
Command: pytest tests/
Error: ModuleNotFoundError: No module named 'pytest'

Orchestrator:
  🧠 Retrieved known correction
  ⚡ Auto-applied: pip install pytest
  ✅ Success (no LLM retry needed!)

Total Time: 3 seconds (instant recovery)
```

---

### Example 3: Preference Adaptation

**After 50 Interactions:**
```
User Pattern Detected:
  - 80% of tasks involve Git
  - Prefers concise responses
  - Always tests after changes
  - Likes code examples

Orchestrator Adaptation:
  - Automatically suggests git status after changes
  - Provides 2-3 line responses instead of paragraphs
  - Includes run_tests step in workflows
  - Always includes code snippets
```

**Before Adaptation:**
```
User: "Fix the bug in auth.py"

Response (250 words):
  "Let me provide a comprehensive explanation...
   First, I'll analyze the authentication module...
   [lengthy explanation]"

User Rating: 👎 (too verbose)
```

**After Adaptation:**
```
User: "Fix the bug in auth.py"

Response (50 words):
  "Fixed JWT validation in line 45:

   # Before
   if not verify_token(token):

   # After
   if not verify_token(token, check_expiry=True):

   Tests passed ✅"

User Rating: 👍
```

---

## Accelerating Learning

### Give Feedback Consistently

The more feedback you provide, the faster the system learns:

**Best Practices:**
- Click 👍 when responses are accurate and helpful
- Click 👎 when responses are incorrect or suboptimal
- Add comments to explain why (optional but very helpful)
- Feedback after every significant interaction

**Impact:**
- 10 feedbacks → Basic preference detection
- 50 feedbacks → Clear pattern recognition
- 100+ feedbacks → Highly personalized responses

---

### Use Regularly and Consistently

Pattern detection requires repeated exposure:

**Recommendations:**
- Use daily instead of sporadically
- Perform similar tasks multiple times
- Let the system observe your workflow

**Learning Timeline:**
- **Week 1:** System collects initial data
- **Week 2-3:** Pattern detection begins
- **Month 1:** Clear performance improvements
- **Month 3:** Expert-level personalization

---

### Vary Task Types

Expose the system to different scenarios:

**Task Categories:**
- Development (coding, debugging, refactoring)
- Testing (unit tests, integration tests)
- DevOps (deployment, monitoring, troubleshooting)
- Documentation (writing, reviewing)
- Data Analysis (queries, visualization)

**Result:** Broader knowledge base, more robust patterns.

---

## Monitoring Learning Progress

### Via Web Interface

The chat interface shows learning indicators:

- **Pattern Reused** badge on responses
- **Response Time** comparison with previous attempts
- **Iteration Count** shows reduction over time

---

### Via Logs

```bash
# Watch learning activity
tail -f /tmp/ai-orchestrator-backend.log | grep -i learning

# Output:
🧠 Retrieved 3 similar experiences for "deploy docker app"
✅ Applying successful pattern from experience #1247
⚡ Skipping failed approach from experience #892
💾 Stored new experience with embedding
```

---

### Via Grafana Dashboard

**Dashboard:** AI-Orchestrator - Learning Performance

**Panels:**
- Experience reuse rate over time
- Average response time reduction
- Success rate evolution
- Pattern application frequency
- Feedback score trends

**Access:** https://grafana.4lb.ca

---

## Future Intelligence

### Projected Capabilities

**After 1 Month:**
- Recognizes your work patterns
- Suggests solutions proactively
- Auto-recovers from 80% of common errors
- 3-4x faster on repeated tasks

**After 3 Months:**
- Anticipates your needs based on context
- Optimizes workflows automatically
- Fully personalized response style
- 5-6x faster on familiar tasks

**After 6 Months:**
- Becomes your expert assistant
- Proposes code improvements proactively
- Detects potential issues before they occur
- Near-instant responses for common tasks

---

## Related Documentation

- [API Reference](../03-api/rest.md) - REST endpoints for learning system
- [Architecture](../02-architecture/core.md) - Learning system architecture
- [Configuration](../05-operations/configuration.md) - Environment setup
- [Monitoring](../05-operations/monitoring.md) - Metrics and dashboards

---

## Troubleshooting

### ChromaDB Not Connected

**Symptom:** Learning system disabled, no pattern reuse

**Solution:**
```bash
# Check ChromaDB status
docker ps | grep chroma

# Restart ChromaDB
docker-compose restart chromadb

# Verify connection
curl http://localhost:8000/api/v1/heartbeat
```

---

### No Patterns Detected

**Symptom:** System not learning from interactions

**Possible Causes:**
- Too few interactions (need 10+ similar queries)
- Feedback not provided
- Learning disabled in config

**Solution:**
```bash
# Check config
grep LEARNING_ENABLED backend/.env

# Enable learning
echo "LEARNING_ENABLED=true" >> backend/.env

# Restart backend
docker-compose restart backend
```

---

### Poor Similarity Matching

**Symptom:** System retrieves irrelevant past experiences

**Solution:**
```bash
# Increase similarity threshold
echo "LEARNING_SIMILARITY_THRESHOLD=0.8" >> backend/.env

# Or switch to better embedding model for code
echo "CHROMA_EMBEDDING_MODEL=qwen3-embedding:8b" >> backend/.env

# Restart to apply changes
docker-compose restart backend
```

---

**Last Updated:** 2026-01-28
**Version:** 7.1
