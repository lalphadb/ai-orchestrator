# PLAN DE RÉPARATION EN PHASES - AI ORCHESTRATOR v6.5 → v7.0

**Objectif:** Corriger tous les bugs, compléter fonctionnalités manquantes, améliorer sécurité/performance
**Timeline:** 6 semaines (ajustable selon priorités)
**Version cible:** v7.0 (production-ready)

---

## PHASE 1 - SÉCURITÉ CRITIQUE 🔴
**Durée:** 2-3 jours
**Blocant:** Oui
**Objectif:** Éliminer risques sécurité majeurs

### Tâche 1.1: Sécurisation secrets (2h)

**Fichiers:**
- `backend/.env`
- `.gitignore`

**Actions:**
```bash
# 1. Ajouter .env au gitignore
echo "backend/.env" >> .gitignore

# 2. Créer template
cp backend/.env backend/.env.example
# Remplacer valeurs réelles par placeholders dans .env.example

# 3. Supprimer .env de l'historique Git
git rm --cached backend/.env
git commit -m "security: remove secrets from version control"

# 4. Régénérer secrets
# Nouveau JWT_SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Nouveau GROQ_API_KEY si compromis
# Aller sur console.groq.com et révoquer/créer
```

**Validation:**
```bash
git log --all --full-history -- "*/.env" # Doit être vide après cleanup
grep -r "gsk_" . --exclude-dir=.git # Aucune clé exposée
```

---

### Tâche 1.2: Authentification WebSocket (3h)

**Fichier:** `backend/app/api/v1/chat.py`

**Modification ligne 111:**
```python
from fastapi import WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from app.core.security import decode_access_token

@router.websocket("/ws")
async def websocket_chat(
    websocket: WebSocket,
    token: str = Query(..., description="JWT token"),
    db: Session = Depends(get_db)
):
    # Valider token avant accept
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=1008, reason="Invalid token")
            return
    except Exception as e:
        await websocket.close(code=1008, reason=f"Auth failed: {str(e)}")
        return

    await websocket.accept()

    # Continuer avec logique existante...
```

**Fichier frontend:** `frontend/src/services/wsClient.js`

**Modification ligne 30:**
```javascript
connect() {
  const token = localStorage.getItem('token')
  if (!token) {
    throw new Error('No authentication token')
  }

  // Ajouter token en query param
  const wsUrl = `${this.baseUrl}?token=${encodeURIComponent(token)}`
  this.ws = new WebSocket(wsUrl)

  // Reste du code...
}
```

**Tests:**
```bash
# Terminal 1: Démarrer backend
cd backend && uvicorn main:app --reload

# Terminal 2: Tester WS sans token
wscat -c ws://localhost:8001/api/v1/chat/ws
# Devrait rejeter avec code 1008

# Terminal 3: Tester avec token valide
# Obtenir token via login puis:
wscat -c "ws://localhost:8001/api/v1/chat/ws?token=eyJ..."
# Devrait accepter connexion
```

---

### Tâche 1.3: Fix bug FeedbackButtons (30min)

**Fichier:** `frontend/src/components/FeedbackButtons.vue`

**Ligne 182-186 (avant):**
```javascript
await learningStore.sendPositiveFeedback(
  props.messageId,
  chatStore.currentConversationId,  // ❌ Undefined
  props.query,
  props.response,
  props.toolsUsed
)
```

**Ligne 182-186 (après):**
```javascript
await learningStore.sendPositiveFeedback(
  props.messageId,
  chatStore.currentConversation?.id,  // ✅ Safe navigation
  props.query,
  props.response,
  props.toolsUsed
)
```

**Répéter pour ligne 224 (negative feedback) et 266 (correction):**
```javascript
// Ligne 224
await learningStore.sendNegativeFeedback(
  props.messageId,
  chatStore.currentConversation?.id,  // ✅
  props.query,
  props.response,
  props.toolsUsed,
  reason.value
)

// Ligne 266
await learningStore.sendCorrection(
  props.messageId,
  chatStore.currentConversation?.id,  // ✅
  props.query,
  correctedResponse.value,
  props.toolsUsed
)
```

**Tests:**
```javascript
// Dans browser console après un message
const messageEl = document.querySelector('.message')
const feedbackBtn = messageEl.querySelector('.feedback-positive')
feedbackBtn.click()
// Vérifier console: pas d'erreur "Cannot read property 'id' of undefined"
```

---

### Tâche 1.4: Gestion erreur tool execution (1h)

**Fichier:** `backend/app/api/v1/tools.py`

**Ligne 61-75 (avant):**
```python
@router.post("/{tool_id}/execute")
async def execute_tool(
    tool_id: str,
    params: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    result = await tools_store.executeTool(tool_id, params)
    return result
```

**Ligne 61-80 (après):**
```python
from app.services.react_engine.tools import ToolResult

@router.post("/{tool_id}/execute")
async def execute_tool(
    tool_id: str,
    params: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    try:
        # Valider que l'outil existe
        if tool_id not in BUILTIN_TOOLS:
            return ToolResult(
                success=False,
                data=None,
                error={
                    "code": "E_TOOL_NOT_FOUND",
                    "message": f"Tool '{tool_id}' does not exist",
                    "recoverable": False
                },
                meta={"duration_ms": 0}
            ).dict()

        result = await tools_store.executeTool(tool_id, params)
        return result

    except Exception as e:
        logger.exception(f"Tool execution failed: {tool_id}")
        return ToolResult(
            success=False,
            data=None,
            error={
                "code": "E_TOOL_EXECUTION",
                "message": str(e),
                "recoverable": False
            },
            meta={"duration_ms": 0}
        ).dict()
```

**Tests:**
```bash
# Test outil inexistant
curl -X POST http://localhost:8001/api/v1/tools/fake_tool/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"param": "value"}'
# Devrait retourner {"success": false, "error": {"code": "E_TOOL_NOT_FOUND"}}

# Test avec params invalides
curl -X POST http://localhost:8001/api/v1/tools/read_file/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"invalid_param": "value"}'
# Devrait retourner erreur propre, pas crash serveur
```

---

### Tâche 1.5: Validation input sanitization (2h)

**Fichier:** `backend/app/services/react_engine/tools.py`

**Ajouter helper de validation path:**
```python
import os
from pathlib import Path

def validate_path(file_path: str, workspace_dir: str) -> tuple[bool, str]:
    """Valide et canonicalise un chemin fichier.

    Returns:
        (is_valid, canonical_path ou error_message)
    """
    try:
        # Résoudre path absolu
        abs_path = Path(file_path).resolve()
        workspace = Path(workspace_dir).resolve()

        # Vérifier pas de traversal
        if not str(abs_path).startswith(str(workspace)):
            return False, f"Path outside workspace: {file_path}"

        return True, str(abs_path)
    except Exception as e:
        return False, f"Invalid path: {str(e)}"
```

**Modifier read_file (ligne ~150):**
```python
async def read_file(file_path: str, **kwargs) -> ToolResult:
    """Lit le contenu d'un fichier."""
    start_time = time.time()

    # Validation path
    is_valid, result = validate_path(file_path, settings.WORKSPACE_DIR)
    if not is_valid:
        return ToolResult(
            success=False,
            data=None,
            error={
                "code": "E_PATH_FORBIDDEN",
                "message": result,
                "recoverable": False
            },
            meta={"duration_ms": int((time.time() - start_time) * 1000)}
        )

    canonical_path = result

    # Reste de la logique avec canonical_path...
```

**Répéter pour:** `write_file`, `list_directory`, `search_directory`, `delete_file`, etc.

**Tests:**
```python
# Test traversal attack
result = await read_file("../../etc/passwd")
assert result.success == False
assert result.error["code"] == "E_PATH_FORBIDDEN"

# Test path valide
result = await read_file("/home/lalpha/orchestrator-workspace/test.txt")
assert result.success == True or result.error["code"] == "E_FILE_NOT_FOUND"
```

---

### Checklist Phase 1

- [ ] `.env` dans .gitignore
- [ ] `.env.example` créé avec placeholders
- [ ] Secrets régénérés
- [ ] Git history nettoyé (secrets supprimés)
- [ ] WebSocket auth implémentée (backend)
- [ ] WebSocket token ajouté (frontend)
- [ ] Tests WS auth passent
- [ ] Bug FeedbackButtons corrigé
- [ ] Tool execution avec gestion erreur
- [ ] Path validation implémentée
- [ ] Tests path traversal passent

**Livrable:** Version v6.5.1 sécurisée

---

## PHASE 2 - BUGS MAJEURS 🟠
**Durée:** 1 semaine
**Objectif:** Stabilité et fonctionnalités critiques

### Tâche 2.1: Persistence feedbacks (4h)

**Étape 1: Modèle database**

**Fichier:** `backend/app/models/database.py`

**Ajouter après classe Tool (ligne 88):**
```python
from datetime import datetime
from enum import Enum as PyEnum

class FeedbackTypeEnum(str, PyEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    CORRECTION = "correction"

class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    feedback_type = Column(String(20), nullable=False)

    # Contexte
    query = Column(Text, nullable=True)
    response = Column(Text, nullable=True)
    corrected_response = Column(Text, nullable=True)
    tools_used = Column(Text, nullable=True)  # JSON
    reason = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relations
    message = relationship("Message", back_populates="feedbacks")
    conversation = relationship("Conversation", back_populates="feedbacks")
    user = relationship("User", back_populates="feedbacks")

# Ajouter dans classe Message (après ligne 53):
feedbacks = relationship("Feedback", back_populates="message", cascade="all, delete-orphan")

# Ajouter dans classe Conversation (après ligne 37):
feedbacks = relationship("Feedback", back_populates="conversation", cascade="all, delete-orphan")

# Ajouter dans classe User (après ligne 23):
feedbacks = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
```

**Étape 2: Migration Alembic**

```bash
cd backend

# Installer Alembic
pip install alembic

# Initialiser
alembic init migrations

# Configurer migrations/env.py
# Importer Base et models
from app.models.database import Base
target_metadata = Base.metadata

# Créer migration
alembic revision --autogenerate -m "add feedback table"

# Appliquer
alembic upgrade head
```

**Étape 3: Modifier FeedbackCollector**

**Fichier:** `backend/app/services/learning/feedback.py`

**Remplacer classe complète:**
```python
from sqlalchemy.orm import Session
from app.models.database import Feedback as FeedbackModel
import json

class FeedbackCollector:
    """Collecte et stocke les feedbacks utilisateur en base de données."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def add_feedback(
        self,
        db: Session,
        message_id: int,
        conversation_id: int,
        user_id: int,
        feedback_type: FeedbackType,
        query: str,
        response: str,
        tools_used: List[Dict[str, Any]],
        corrected_response: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Feedback:
        """Ajoute un feedback en base de données."""

        # Créer feedback DB
        feedback_db = FeedbackModel(
            message_id=message_id,
            conversation_id=conversation_id,
            user_id=user_id,
            feedback_type=feedback_type.value,
            query=query,
            response=response,
            corrected_response=corrected_response,
            tools_used=json.dumps(tools_used),
            reason=reason
        )

        db.add(feedback_db)
        db.commit()
        db.refresh(feedback_db)

        # Retourner objet Feedback pour compatibilité
        return Feedback(
            feedback_type=feedback_type,
            message_id=str(message_id),
            conversation_id=str(conversation_id),
            query=query,
            response=response,
            tools_used=tools_used,
            corrected_response=corrected_response,
            reason=reason,
            timestamp=feedback_db.created_at.isoformat()
        )

    def get_feedback_stats(
        self,
        db: Session,
        user_id: Optional[int] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Récupère les stats de feedback."""
        from datetime import datetime, timedelta

        query = db.query(FeedbackModel)

        if user_id:
            query = query.filter(FeedbackModel.user_id == user_id)

        # Filtrer par période
        since = datetime.utcnow() - timedelta(hours=hours)
        query = query.filter(FeedbackModel.created_at >= since)

        feedbacks = query.all()

        # Calculer stats
        total = len(feedbacks)
        positive = len([f for f in feedbacks if f.feedback_type == "positive"])
        negative = len([f for f in feedbacks if f.feedback_type == "negative"])
        corrections = len([f for f in feedbacks if f.feedback_type == "correction"])

        return {
            "total": total,
            "positive": positive,
            "negative": negative,
            "corrections": corrections,
            "period_hours": hours
        }
```

**Étape 4: Modifier endpoints learning**

**Fichier:** `backend/app/api/v1/learning.py`

**Ajouter dépendance DB aux routes:**
```python
from sqlalchemy.orm import Session
from app.core.database import get_db

@router.post("/feedback")
async def submit_feedback(
    feedback: FeedbackSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Ajouter feedback en DB
    feedback_obj = feedback_collector.add_feedback(
        db=db,
        message_id=int(feedback.message_id),
        conversation_id=int(feedback.conversation_id),
        user_id=current_user.id,
        feedback_type=feedback.feedback_type,
        query=feedback.query,
        response=feedback.response,
        tools_used=feedback.tools_used or [],
        corrected_response=feedback.corrected_response,
        reason=feedback.reason
    )

    # Stocker dans ChromaDB (logique existante)...

    return {"status": "success", "feedback_id": feedback_obj.message_id}

@router.get("/feedback/stats")
async def get_feedback_stats(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stats = feedback_collector.get_feedback_stats(
        db=db,
        user_id=current_user.id,
        hours=hours
    )
    return stats
```

**Tests:**
```bash
# Soumettre feedback
curl -X POST http://localhost:8001/api/v1/learning/feedback \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "message_id": "123",
    "conversation_id": "456",
    "feedback_type": "positive",
    "query": "test",
    "response": "result"
  }'

# Vérifier en DB
sqlite3 backend/ai_orchestrator.db "SELECT * FROM feedbacks;"

# Redémarrer serveur
sudo systemctl restart ai-orchestrator

# Vérifier stats (devrait conserver données)
curl http://localhost:8001/api/v1/learning/feedback/stats?hours=24 \
  -H "Authorization: Bearer $TOKEN"
```

---

### Tâche 2.2: Implémenter get_top_patterns() (2h)

**Fichier:** `backend/app/services/learning/memory.py`

**Ajouter méthode après search_patterns (ligne ~120):**
```python
def get_top_patterns(self, limit: int = 10) -> List[Dict[str, Any]]:
    """Récupère les patterns les plus utilisés.

    Trie par usage_count descendant.
    """
    try:
        if not self.client:
            return []

        # Récupérer tous les patterns
        results = self.patterns.get(
            include=["metadatas", "documents"]
        )

        if not results or not results["metadatas"]:
            return []

        # Convertir en liste de dicts
        patterns = []
        for i, metadata in enumerate(results["metadatas"]):
            patterns.append({
                "pattern": results["documents"][i],
                "usage_count": metadata.get("usage_count", 0),
                "context": metadata.get("context", ""),
                "created_at": metadata.get("created_at", "")
            })

        # Trier par usage_count descendant
        patterns.sort(key=lambda x: x["usage_count"], reverse=True)

        return patterns[:limit]

    except Exception as e:
        self.logger.error(f"Erreur get_top_patterns: {e}")
        return []
```

**Fichier:** `backend/app/api/v1/learning.py`

**Modifier ligne 186:**
```python
@router.get("/patterns", response_model=PatternsResponse)
async def get_patterns(
    query: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50)
):
    """Récupère les patterns appris."""
    if query:
        patterns = learning_memory.search_patterns(query, limit)
    else:
        patterns = learning_memory.get_top_patterns(limit)  # ✅ Implémenté

    return PatternsResponse(patterns=patterns)
```

**Tests:**
```bash
# Ajouter quelques patterns
curl -X POST http://localhost:8001/api/v1/learning/feedback \
  -H "Authorization: Bearer $TOKEN" \
  -d '{...}'  # Soumettre feedbacks positifs

# Récupérer top patterns
curl http://localhost:8001/api/v1/learning/patterns?limit=5 \
  -H "Authorization: Bearer $TOKEN"
# Devrait retourner array de patterns triés par usage
```

---

### Tâche 2.3: Feedback → score update ChromaDB (3h)

**Fichier:** `backend/app/services/learning/memory.py`

**Ajouter méthode après store_experience:**
```python
def update_experience_score(self, experience_id: str, score_delta: int = 1):
    """Met à jour le score d'une expérience existante.

    Args:
        experience_id: ID de l'expérience dans ChromaDB
        score_delta: Increment (positif) ou decrement (négatif)
    """
    try:
        if not self.client:
            return

        # Récupérer expérience actuelle
        result = self.experiences.get(
            ids=[experience_id],
            include=["metadatas"]
        )

        if not result or not result["metadatas"]:
            self.logger.warning(f"Experience {experience_id} not found")
            return

        # Calculer nouveau score
        current_score = result["metadatas"][0].get("score", 0)
        new_score = max(0, current_score + score_delta)  # Min 0

        # Mettre à jour metadata
        self.experiences.update(
            ids=[experience_id],
            metadatas=[{
                **result["metadatas"][0],
                "score": new_score,
                "last_feedback": datetime.now().isoformat()
            }]
        )

        self.logger.info(f"Updated experience {experience_id}: score {current_score} → {new_score}")

    except Exception as e:
        self.logger.error(f"Erreur update score: {e}")
```

**Fichier:** `backend/app/api/v1/learning.py`

**Modifier submit_feedback ligne 130:**
```python
@router.post("/feedback")
async def submit_feedback(feedback: FeedbackSubmission, ...):
    # ... validation ...

    if feedback.feedback_type == FeedbackType.POSITIVE:
        # Chercher experience_id correspondant
        similar = learning_memory.search_similar_experiences(
            query=feedback.query,
            limit=1
        )

        if similar and len(similar) > 0:
            # Récupérer ID depuis metadata ou construire
            experience_id = similar[0].get("id")
            if experience_id:
                learning_memory.update_experience_score(
                    experience_id=experience_id,
                    score_delta=1
                )
                logger.info(f"Positive feedback → score +1 for experience {experience_id}")

    elif feedback.feedback_type == FeedbackType.NEGATIVE:
        # Optionnel: décrémenter score
        similar = learning_memory.search_similar_experiences(
            query=feedback.query,
            limit=1
        )

        if similar and len(similar) > 0:
            experience_id = similar[0].get("id")
            if experience_id:
                learning_memory.update_experience_score(
                    experience_id=experience_id,
                    score_delta=-1
                )

    # ... reste du code ...
```

**Note:** ChromaDB `get()` et `update()` nécessitent que les IDs soient stockés. Vérifier dans `store_experience()` que les IDs sont bien générés et stockés.

**Tests:**
```python
# Script test
import chromadb

client = chromadb.HttpClient(host="localhost", port=8000)
experiences = client.get_collection("experiences")

# Créer expérience test
exp_id = "test_exp_001"
experiences.add(
    ids=[exp_id],
    documents=["Test query"],
    metadatas=[{"score": 5, "result": "success"}]
)

# Simuler feedback positif
result = experiences.get(ids=[exp_id], include=["metadatas"])
new_score = result["metadatas"][0]["score"] + 1

experiences.update(
    ids=[exp_id],
    metadatas=[{**result["metadatas"][0], "score": new_score}]
)

# Vérifier
updated = experiences.get(ids=[exp_id], include=["metadatas"])
assert updated["metadatas"][0]["score"] == 6
print("✅ Score update works")
```

---

### Tâche 2.4: Indices base de données (1h)

**Fichier:** `backend/app/models/database.py`

**Après toutes les définitions de classes, avant `Base.metadata.create_all()` (si présent):**

```python
from sqlalchemy import Index

# Indices pour Message
Index('ix_message_conversation', Message.conversation_id)
Index('ix_message_created', Message.created_at)

# Indices pour Conversation
Index('ix_conversation_user', Conversation.user_id)
Index('ix_conversation_updated', Conversation.updated_at)

# Indices pour Feedback (nouvelle table)
Index('ix_feedback_message', Feedback.message_id)
Index('ix_feedback_conversation', Feedback.conversation_id)
Index('ix_feedback_user', Feedback.user_id)
Index('ix_feedback_created', Feedback.created_at)
```

**Migration:**
```bash
cd backend

# Créer migration
alembic revision --autogenerate -m "add database indexes"

# Vérifier le fichier généré
cat migrations/versions/*_add_database_indexes.py

# Appliquer
alembic upgrade head
```

**Validation:**
```bash
sqlite3 backend/ai_orchestrator.db

# Lister tous les indices
.indexes

# Devrait afficher:
# ix_message_conversation
# ix_message_created
# ix_conversation_user
# ix_conversation_updated
# etc.

# Analyser query plan
EXPLAIN QUERY PLAN
SELECT * FROM messages
WHERE conversation_id = 123
ORDER BY created_at DESC;

# Devrait utiliser "USING INDEX ix_message_conversation"
```

---

### Tâche 2.5: Retry ChromaDB avec backoff (2h)

**Fichier:** `backend/app/services/learning/memory.py`

**Installer dependency:**
```bash
pip install tenacity
echo "tenacity>=8.2.0" >> backend/requirements.txt
```

**Modifier __init__ (ligne 34):**
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import chromadb
from chromadb.errors import ChromaError

class LearningMemory:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.experiences = None
        self.patterns = None
        self.preferences = None

        # Tenter connexion avec retry
        self._connect_with_retry()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, ChromaError)),
        reraise=True
    )
    def _connect_with_retry(self):
        """Connexion ChromaDB avec retry automatique."""
        try:
            chroma_host = os.getenv("CHROMA_HOST", "localhost")
            chroma_port = int(os.getenv("CHROMA_PORT", "8000"))

            self.logger.info(f"Connecting to ChromaDB at {chroma_host}:{chroma_port}...")

            self.client = chromadb.HttpClient(
                host=chroma_host,
                port=chroma_port
            )

            # Initialiser collections
            self._init_collections()

            self.logger.info("ChromaDB connection established")

        except Exception as e:
            self.logger.error(f"ChromaDB connection failed: {e}")
            raise

    def reconnect(self):
        """Force reconnexion (si healthcheck détecte problème)."""
        self.client = None
        self._connect_with_retry()
```

**Ajouter healthcheck wrapper pour méthodes:**
```python
def _ensure_connected(func):
    """Décorateur pour assurer connexion ChromaDB."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.client:
            try:
                self._connect_with_retry()
            except Exception as e:
                self.logger.error(f"Reconnection failed: {e}")
                return None  # ou valeur par défaut selon méthode

        return func(self, *args, **kwargs)

    return wrapper

# Appliquer à toutes les méthodes
@_ensure_connected
def store_experience(self, ...):
    # ...

@_ensure_connected
def search_similar_experiences(self, ...):
    # ...

# etc.
```

**Tests:**
```bash
# Terminal 1: Arrêter ChromaDB
docker stop chromadb

# Terminal 2: Démarrer backend
cd backend && uvicorn main:app --reload
# Devrait logger 3 tentatives de connexion puis erreur

# Terminal 1: Redémarrer ChromaDB
docker start chromadb

# Terminal 2: Appeler endpoint learning
curl http://localhost:8001/api/v1/learning/stats -H "Authorization: Bearer $TOKEN"
# Devrait se reconnecter automatiquement
```

---

### Checklist Phase 2

- [ ] Table Feedback créée en DB
- [ ] Alembic configuré et migration initiale
- [ ] FeedbackCollector utilise DB
- [ ] Feedbacks persistent au redémarrage
- [ ] get_top_patterns() implémenté
- [ ] Endpoint /learning/patterns fonctionne sans query
- [ ] Feedback positif met à jour score ChromaDB
- [ ] Indices DB créés
- [ ] Query performance améliorée (vérifier EXPLAIN)
- [ ] Retry ChromaDB avec tenacity
- [ ] Reconnexion automatique fonctionne

**Livrable:** Version v6.6 avec learning complet

---

## PHASE 3 - AMÉLIORATIONS UX 🟡
**Durée:** 2 semaines
**Objectif:** Interface utilisateur complète et fluide

### Tâche 3.1: Dashboard apprentissage (8h)

**Étape 1: Créer vue**

**Fichier:** `frontend/src/views/LearningView.vue`

```vue
<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-white mb-2">Apprentissage IA</h1>
        <p class="text-gray-400">Statistiques et patterns appris par le système</p>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <!-- Total Feedback -->
        <div class="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-medium text-gray-400">Total Feedbacks</h3>
            <span class="text-2xl">📊</span>
          </div>
          <div class="text-3xl font-bold text-white">
            {{ learningStats?.total_experiences || 0 }}
          </div>
        </div>

        <!-- Positive Rate -->
        <div class="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-medium text-gray-400">Taux Positif</h3>
            <span class="text-2xl">👍</span>
          </div>
          <div class="text-3xl font-bold text-green-400">
            {{ positiveRate }}%
          </div>
        </div>

        <!-- Patterns Appris -->
        <div class="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-medium text-gray-400">Patterns</h3>
            <span class="text-2xl">🧠</span>
          </div>
          <div class="text-3xl font-bold text-blue-400">
            {{ learningStats?.total_patterns || 0 }}
          </div>
        </div>

        <!-- Corrections -->
        <div class="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-medium text-gray-400">Corrections</h3>
            <span class="text-2xl">✏️</span>
          </div>
          <div class="text-3xl font-bold text-orange-400">
            {{ feedbackStats?.corrections || 0 }}
          </div>
        </div>
      </div>

      <!-- Feedback Timeline -->
      <div class="bg-gray-900/50 border border-gray-800 rounded-xl p-6 mb-8">
        <h2 class="text-xl font-bold text-white mb-4">Activité (24h)</h2>
        <div class="space-y-2">
          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-400">Positifs</span>
            <div class="flex items-center gap-2">
              <div class="w-64 bg-gray-800 rounded-full h-2">
                <div
                  class="bg-green-500 h-2 rounded-full"
                  :style="{width: `${(feedbackStats?.positive / feedbackStats?.total * 100) || 0}%`}"
                ></div>
              </div>
              <span class="text-white font-medium w-12 text-right">
                {{ feedbackStats?.positive || 0 }}
              </span>
            </div>
          </div>

          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-400">Négatifs</span>
            <div class="flex items-center gap-2">
              <div class="w-64 bg-gray-800 rounded-full h-2">
                <div
                  class="bg-red-500 h-2 rounded-full"
                  :style="{width: `${(feedbackStats?.negative / feedbackStats?.total * 100) || 0}%`}"
                ></div>
              </div>
              <span class="text-white font-medium w-12 text-right">
                {{ feedbackStats?.negative || 0 }}
              </span>
            </div>
          </div>

          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-400">Corrections</span>
            <div class="flex items-center gap-2">
              <div class="w-64 bg-gray-800 rounded-full h-2">
                <div
                  class="bg-orange-500 h-2 rounded-full"
                  :style="{width: `${(feedbackStats?.corrections / feedbackStats?.total * 100) || 0}%`}"
                ></div>
              </div>
              <span class="text-white font-medium w-12 text-right">
                {{ feedbackStats?.corrections || 0 }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Top Patterns -->
      <div class="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
        <h2 class="text-xl font-bold text-white mb-4">Patterns les Plus Utilisés</h2>

        <div v-if="topPatterns.length === 0" class="text-center py-12 text-gray-500">
          Aucun pattern appris pour le moment
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="(pattern, index) in topPatterns"
            :key="index"
            class="bg-gray-800/50 border border-gray-700 rounded-lg p-4 hover:border-gray-600 transition-colors"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <div class="text-sm font-mono text-gray-300 mb-2">
                  {{ pattern.pattern }}
                </div>
                <div class="text-xs text-gray-500">
                  Contexte: {{ pattern.context || 'N/A' }}
                </div>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-xs text-gray-400">Utilisé</span>
                <span class="text-lg font-bold text-blue-400">
                  {{ pattern.usage_count }}×
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useLearningStore } from '@/stores/learning'

const learningStore = useLearningStore()

const learningStats = ref(null)
const feedbackStats = ref(null)
const topPatterns = ref([])

const positiveRate = computed(() => {
  if (!feedbackStats.value || feedbackStats.value.total === 0) return 0
  return Math.round((feedbackStats.value.positive / feedbackStats.value.total) * 100)
})

async function loadData() {
  try {
    // Charger stats
    learningStats.value = await learningStore.fetchLearningStats()
    feedbackStats.value = await learningStore.fetchFeedbackStats(24)

    // Charger top patterns
    const response = await fetch('/api/v1/learning/patterns?limit=10', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    const data = await response.json()
    topPatterns.value = data.patterns || []
  } catch (error) {
    console.error('Failed to load learning data:', error)
  }
}

onMounted(() => {
  loadData()
})
</script>
```

**Étape 2: Ajouter route**

**Fichier:** `frontend/src/router/index.js`

```javascript
import LearningView from '@/views/LearningView.vue'

const routes = [
  // ... routes existantes ...
  {
    path: '/learning',
    name: 'Learning',
    component: LearningView,
    meta: { requiresAuth: true }
  }
]
```

**Étape 3: Ajouter au menu**

**Fichier:** `frontend/src/components/ConversationSidebar.vue` (ou layout principal)

```vue
<!-- Ajouter bouton navigation -->
<router-link
  to="/learning"
  class="flex items-center gap-3 px-4 py-2 text-gray-300 hover:bg-gray-800 rounded-lg transition-colors"
>
  <span class="text-xl">🧠</span>
  <span>Apprentissage</span>
</router-link>
```

---

### Tâche 3.2: Consolidation MessageInput (3h)

**Étape 1: Analyser différences**

```bash
cd frontend/src/components
diff MessageInput.vue ChatInput.vue
# Identifier fonctionnalités uniques à chaque composant
```

**Étape 2: Créer composant unifié**

**Fichier:** `frontend/src/components/UnifiedMessageInput.vue`

```vue
<template>
  <div class="message-input-container">
    <!-- Model Selector -->
    <div v-if="showModelSelector" class="mb-3">
      <select
        v-model="selectedModel"
        class="w-full px-4 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-white"
      >
        <option v-for="model in availableModels" :key="model" :value="model">
          {{ model }}
        </option>
      </select>
    </div>

    <!-- Textarea -->
    <div class="relative">
      <textarea
        ref="textareaRef"
        v-model="message"
        @keydown.enter.exact.prevent="handleSubmit"
        @keydown.enter.shift.exact="handleNewLine"
        :placeholder="placeholder"
        :disabled="disabled"
        class="w-full px-4 py-3 bg-gray-900/50 border border-gray-700 rounded-lg text-white resize-none focus:outline-none focus:border-blue-500"
        rows="3"
      ></textarea>

      <!-- Action Buttons -->
      <div class="absolute bottom-3 right-3 flex items-center gap-2">
        <!-- Export Menu (optionnel) -->
        <button
          v-if="showExport"
          @click="toggleExportMenu"
          class="p-2 text-gray-400 hover:text-white transition-colors"
          title="Export conversation"
        >
          📥
        </button>

        <!-- Send Button -->
        <button
          @click="handleSubmit"
          :disabled="!message.trim() || disabled"
          class="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
        >
          {{ submitLabel }}
        </button>
      </div>
    </div>

    <!-- Export Dropdown -->
    <div v-if="showExportMenu" class="mt-2 bg-gray-900 border border-gray-700 rounded-lg p-2">
      <button
        @click="exportAs('json')"
        class="w-full text-left px-3 py-2 hover:bg-gray-800 rounded text-white text-sm"
      >
        Export JSON
      </button>
      <button
        @click="exportAs('markdown')"
        class="w-full text-left px-3 py-2 hover:bg-gray-800 rounded text-white text-sm"
      >
        Export Markdown
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useChatStore } from '@/stores/chat'

const props = defineProps({
  placeholder: {
    type: String,
    default: 'Tapez votre message... (Shift+Enter pour nouvelle ligne)'
  },
  disabled: {
    type: Boolean,
    default: false
  },
  showModelSelector: {
    type: Boolean,
    default: true
  },
  showExport: {
    type: Boolean,
    default: false
  },
  submitLabel: {
    type: String,
    default: 'Envoyer'
  }
})

const emit = defineEmits(['submit'])

const chatStore = useChatStore()

const message = ref('')
const selectedModel = ref(chatStore.currentModel)
const textareaRef = ref(null)
const showExportMenu = ref(false)

const availableModels = ref([])

// Watch model changes
watch(() => chatStore.currentModel, (newModel) => {
  selectedModel.value = newModel
})

watch(selectedModel, (newModel) => {
  chatStore.currentModel = newModel
})

// Load models
async function loadModels() {
  await chatStore.fetchModels()
  availableModels.value = chatStore.availableModels
}

function handleSubmit() {
  if (!message.value.trim() || props.disabled) return

  emit('submit', {
    message: message.value,
    model: selectedModel.value
  })

  message.value = ''
  textareaRef.value?.focus()
}

function handleNewLine(event) {
  // Shift+Enter insère newline (comportement par défaut)
}

function toggleExportMenu() {
  showExportMenu.value = !showExportMenu.value
}

function exportAs(format) {
  const content = chatStore.exportConversation(format)
  const blob = new Blob([content], {
    type: format === 'json' ? 'application/json' : 'text/markdown'
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `conversation-${Date.now()}.${format === 'json' ? 'json' : 'md'}`
  a.click()
  URL.revokeObjectURL(url)

  showExportMenu.value = false

  // TODO: Ajouter toast notification
}

onMounted(() => {
  loadModels()
})
</script>
```

**Étape 3: Remplacer usages**

**Fichier:** `frontend/src/views/ChatView.vue`

```vue
<script setup>
// Remplacer
import MessageInput from '@/components/MessageInput.vue'

// Par
import UnifiedMessageInput from '@/components/UnifiedMessageInput.vue'
</script>

<template>
  <!-- Remplacer -->
  <MessageInput @submit="handleSend" />

  <!-- Par -->
  <UnifiedMessageInput
    @submit="handleSend"
    :show-export="true"
    :disabled="chat.isStreaming"
  />
</template>
```

**Fichier:** `frontend/src/views/ToolsView.vue`

```vue
<!-- Similaire, utiliser UnifiedMessageInput avec props appropriées -->
<UnifiedMessageInput
  @submit="executeTestTool"
  :show-model-selector="false"
  :show-export="false"
  submit-label="Exécuter"
  placeholder="Paramètres JSON..."
/>
```

**Étape 4: Supprimer anciens composants**

```bash
git rm frontend/src/components/MessageInput.vue
git rm frontend/src/components/ChatInput.vue
git commit -m "refactor: consolidate message input components"
```

---

### Tâche 3.3: Feedback actions UI (4h)

**Fichier:** `frontend/src/components/RunInspector.vue`

**Modifier boutons re-verify et repair (ligne 296-315):**

```vue
<template>
  <!-- ... existing code ... -->

  <div class="flex gap-2">
    <!-- Re-verify Button -->
    <button
      @click="handleReVerify"
      :disabled="isReVerifying"
      class="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center gap-2"
    >
      <span v-if="isReVerifying" class="animate-spin">⟳</span>
      <span v-else>🔍</span>
      {{ isReVerifying ? 'Vérification...' : 'Re-verify' }}
    </button>

    <!-- Repair Button -->
    <button
      @click="handleRepair"
      :disabled="isRepairing"
      class="px-4 py-2 bg-orange-600 hover:bg-orange-500 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center gap-2"
    >
      <span v-if="isRepairing" class="animate-spin">⟳</span>
      <span v-else>🔧</span>
      {{ isRepairing ? 'Réparation...' : 'Repair' }}
    </button>
  </div>

  <!-- Toast Notification -->
  <Transition name="fade">
    <div
      v-if="toast.show"
      :class="[
        'fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-lg',
        toast.type === 'success' ? 'bg-green-600' : 'bg-red-600',
        'text-white font-medium'
      ]"
    >
      {{ toast.message }}
    </div>
  </Transition>
</template>

<script setup>
import { ref } from 'vue'
import { useChatStore } from '@/stores/chat'

const chat = useChatStore()

const isReVerifying = ref(false)
const isRepairing = ref(false)
const toast = ref({
  show: false,
  message: '',
  type: 'success'
})

async function handleReVerify() {
  isReVerifying.value = true

  try {
    await chat.rerunVerification()
    showToast('Vérification relancée avec succès', 'success')
  } catch (error) {
    showToast(`Échec de la vérification: ${error.message}`, 'error')
  } finally {
    isReVerifying.value = false
  }
}

async function handleRepair() {
  isRepairing.value = true

  try {
    await chat.forceRepair()
    showToast('Réparation lancée avec succès', 'success')
  } catch (error) {
    showToast(`Échec de la réparation: ${error.message}`, 'error')
  } finally {
    isRepairing.value = false
  }
}

function showToast(message, type = 'success') {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
```

**Similaire pour export conversation:**

**Fichier:** `frontend/src/components/UnifiedMessageInput.vue` (déjà fait ci-dessus)

```javascript
function exportAs(format) {
  // ... export logic ...

  // Ajouter feedback
  showToast(`Conversation exportée en ${format.toUpperCase()}`, 'success')
}
```

---

### Tâche 3.4: Rate limiting middleware (3h)

**Installer dependency:**
```bash
cd backend
pip install slowapi
echo "slowapi>=0.1.9" >> requirements.txt
```

**Fichier:** `backend/main.py`

**Ajouter après imports:**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import settings

# Créer limiter
limiter = Limiter(key_func=get_remote_address)

# Dans create_app():
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

**Fichier:** `backend/app/api/v1/chat.py`

**Ajouter rate limit aux endpoints:**
```python
from slowapi import Limiter
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)

@router.post("/chat")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def chat(
    request: Request,  # Requis pour slowapi
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # ... existing logic ...
```

**Répéter pour:**
- `/chat/simple`
- `/learning/feedback`
- `/tools/{tool_id}/execute`

**Tests:**
```bash
# Script pour tester rate limiting
for i in {1..35}; do
  echo "Request $i"
  curl -X POST http://localhost:8001/api/v1/chat \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"message": "test"}' &
done

wait

# Après 30 requêtes, devrait retourner 429 Too Many Requests
```

---

### Checklist Phase 3

- [ ] LearningView.vue créée
- [ ] Route /learning ajoutée
- [ ] Menu navigation mis à jour
- [ ] Dashboard affiche stats
- [ ] Top patterns affichés
- [ ] UnifiedMessageInput créé
- [ ] MessageInput.vue supprimé
- [ ] ChatInput.vue supprimé
- [ ] Tous usages migrés
- [ ] RunInspector avec loading states
- [ ] Toast notifications implémentées
- [ ] Export avec feedback
- [ ] slowapi installé
- [ ] Rate limiting actif
- [ ] Tests rate limit passent

**Livrable:** Version v6.7 avec UX complète

---

## PHASE 4 - QUALITÉ CODE 🟢
**Durée:** 2 semaines
**Objectif:** Tests, documentation, optimisations

### Tâche 4.1: Tests backend (1 semaine)

**Configuration pytest:**

**Fichier:** `backend/tests/conftest.py`

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.database import Base
from app.core.database import get_db
from main import app
from fastapi.testclient import TestClient

# DB test en mémoire
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    """Créer DB test pour chaque test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    """Client API test."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def auth_token(client):
    """Token JWT pour tests authentifiés."""
    # Créer user test
    response = client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "password": "testpass123"
    })

    # Login
    response = client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "testpass123"
    })

    return response.json()["access_token"]
```

**Tests API:**

**Fichier:** `backend/tests/test_api_chat.py`

```python
def test_chat_endpoint_requires_auth(client):
    """Test que /chat nécessite authentification."""
    response = client.post("/api/v1/chat", json={"message": "test"})
    assert response.status_code == 401

def test_chat_endpoint_with_auth(client, auth_token):
    """Test chat avec auth."""
    response = client.post(
        "/api/v1/chat",
        json={"message": "Hello"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data

def test_rate_limiting(client, auth_token):
    """Test rate limiting."""
    # Envoyer 31 requêtes (limite = 30)
    for i in range(31):
        response = client.post(
            "/api/v1/chat",
            json={"message": f"test {i}"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

    # 31ème devrait être rate limited
    assert response.status_code == 429
```

**Tests outils:**

**Fichier:** `backend/tests/test_tools.py`

```python
import pytest
from app.services.react_engine.tools import read_file, write_file, list_directory

@pytest.mark.asyncio
async def test_read_file_success(tmp_path):
    """Test lecture fichier."""
    # Créer fichier test
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello world")

    result = await read_file(str(test_file))

    assert result.success == True
    assert "hello world" in result.data["content"]

@pytest.mark.asyncio
async def test_read_file_not_found():
    """Test fichier inexistant."""
    result = await read_file("/nonexistent/file.txt")

    assert result.success == False
    assert result.error["code"] == "E_FILE_NOT_FOUND"
    assert result.error["recoverable"] == True

@pytest.mark.asyncio
async def test_path_traversal_blocked():
    """Test protection path traversal."""
    result = await read_file("../../etc/passwd")

    assert result.success == False
    assert result.error["code"] == "E_PATH_FORBIDDEN"
```

**Lancer tests:**
```bash
cd backend
pytest tests/ -v --cov=app --cov-report=html
# Ouvrir htmlcov/index.html pour rapport couverture
```

---

### Tâche 4.2: Tests frontend (3 jours)

**Configuration vitest:**

```bash
cd frontend
npm install -D vitest @vue/test-utils jsdom
```

**Fichier:** `frontend/vitest.config.js`

```javascript
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'jsdom',
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

**Tests stores:**

**Fichier:** `frontend/tests/stores/chat.test.js`

```javascript
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useChatStore } from '@/stores/chat'

describe('Chat Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initializes with empty state', () => {
    const store = useChatStore()
    expect(store.conversations).toEqual([])
    expect(store.currentConversation).toBeNull()
  })

  it('selects conversation', () => {
    const store = useChatStore()
    store.conversations = [
      { id: '1', title: 'Test 1', messages: [] },
      { id: '2', title: 'Test 2', messages: [] }
    ]

    store.selectConversation('1')
    expect(store.currentConversation.id).toBe('1')
  })

  it('exports conversation as JSON', () => {
    const store = useChatStore()
    store.currentConversation = {
      id: '1',
      title: 'Test',
      messages: [
        { role: 'user', content: 'Hello' },
        { role: 'assistant', content: 'Hi!' }
      ]
    }

    const json = store.exportConversation('json')
    const parsed = JSON.parse(json)

    expect(parsed.title).toBe('Test')
    expect(parsed.messages).toHaveLength(2)
  })
})
```

**Tests composants:**

**Fichier:** `frontend/tests/components/FeedbackButtons.test.js`

```javascript
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import FeedbackButtons from '@/components/FeedbackButtons.vue'
import { createPinia, setActivePinia } from 'pinia'

describe('FeedbackButtons', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders three buttons', () => {
    const wrapper = mount(FeedbackButtons, {
      props: {
        messageId: '123',
        query: 'test',
        response: 'result',
        toolsUsed: []
      }
    })

    expect(wrapper.findAll('button')).toHaveLength(3)
  })

  it('disables buttons after feedback', async () => {
    const wrapper = mount(FeedbackButtons, {
      props: {
        messageId: '123',
        query: 'test',
        response: 'result',
        toolsUsed: []
      }
    })

    const positiveBtn = wrapper.find('.feedback-positive')
    await positiveBtn.trigger('click')

    // Tous les boutons devraient être désactivés
    wrapper.findAll('button').forEach(btn => {
      expect(btn.attributes('disabled')).toBeDefined()
    })
  })
})
```

**Lancer tests:**
```bash
cd frontend
npm run test
# ou
vitest --coverage
```

---

### Tâche 4.3: Optimisations performance (4 jours)

**1. Connection pooling Ollama**

**Fichier:** `backend/app/services/ollama/client.py`

```python
class OllamaClient:
    def __init__(self):
        self.base_url = settings.OLLAMA_URL
        self.timeout = httpx.Timeout(300.0, connect=10.0)

        # Créer client persistant avec pool
        self._http_client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(
                max_connections=20,
                max_keepalive_connections=10
            )
        )

    async def close(self):
        """Fermer client HTTP."""
        await self._http_client.aclose()

    async def generate(self, model: str, prompt: str, **kwargs):
        """Utilise client persistant."""
        # Remplacer:
        # async with httpx.AsyncClient(timeout=self.timeout) as client:

        # Par:
        response = await self._http_client.post(
            f"{self.base_url}/api/generate",
            json={"model": model, "prompt": prompt, **kwargs}
        )
        # ...

# Dans main.py - cleanup au shutdown
from app.services.ollama.client import ollama_client

@app.on_event("shutdown")
async def shutdown():
    await ollama_client.close()
```

**2. Simplifier model detection**

**Backend - ajouter flag:**

**Fichier:** `backend/app/api/v1/system.py`

```python
@router.get("/models")
async def get_models():
    models = await ollama_client.list_models()

    # Ajouter metadata
    for model in models:
        model["contains_model_list"] = False  # Flag pour frontend

    return {"models": models}
```

**Frontend - remplacer regex par flag:**

**Fichier:** `frontend/src/components/MessageList.vue`

```vue
<script setup>
// Supprimer les 500 lignes de regex (ligne 226-443)

// Remplacer par:
function shouldDisplayAsModelList(message) {
  // Si backend a flag
  if (message.metadata?.contains_model_list) {
    return true
  }

  // Sinon simple heuristic
  return message.content.includes('Model:') && message.content.includes('Size:')
}
</script>
```

**3. Pagination conversations**

**Backend:**

**Fichier:** `backend/app/api/v1/conversations.py`

```python
@router.get("/conversations")
async def get_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conversations = db.query(Conversation)\
        .filter(Conversation.user_id == current_user.id)\
        .order_by(Conversation.updated_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

    total = db.query(Conversation)\
        .filter(Conversation.user_id == current_user.id)\
        .count()

    return {
        "conversations": conversations,
        "total": total,
        "skip": skip,
        "limit": limit
    }
```

**Frontend - infinite scroll:**

**Fichier:** `frontend/src/stores/chat.js`

```javascript
async fetchConversations(append = false) {
  const skip = append ? this.conversations.length : 0
  const limit = 50

  const response = await api.get(`/conversations?skip=${skip}&limit=${limit}`)

  if (append) {
    this.conversations.push(...response.data.conversations)
  } else {
    this.conversations = response.data.conversations
  }

  this.hasMoreConversations = response.data.total > this.conversations.length
}
```

---

### Checklist Phase 4

- [ ] pytest configuré
- [ ] Tests API auth
- [ ] Tests API chat
- [ ] Tests tools
- [ ] Tests rate limiting
- [ ] Coverage > 70%
- [ ] vitest configuré
- [ ] Tests stores
- [ ] Tests composants
- [ ] Connection pooling Ollama
- [ ] Model detection simplifiée
- [ ] Pagination conversations
- [ ] ESLint configuré
- [ ] Pre-commit hooks

**Livrable:** Version v7.0 production-ready

---

## RÉCAPITULATIF GLOBAL

### Timeline

| Phase | Durée | Effort | Dépendances |
|-------|-------|--------|-------------|
| Phase 1 - Sécurité | 2-3 jours | 8h | Aucune |
| Phase 2 - Bugs majeurs | 1 semaine | 12h | Phase 1 complète |
| Phase 3 - UX | 2 semaines | 18h | Phase 2 complète |
| Phase 4 - Qualité | 2 semaines | 24h | Phase 3 complète |

**Total:** ~6 semaines, ~62 heures développement

### Versions

- **v6.5 (actuel):** Fonctionnel avec bugs
- **v6.5.1 (Phase 1):** Sécurisé
- **v6.6 (Phase 2):** Stable et complet
- **v6.7 (Phase 3):** UX moderne
- **v7.0 (Phase 4):** Production-ready

### Priorités ajustables

**Si temps limité, ordre recommandé:**

1. ✅ Phase 1 (critique sécurité)
2. ✅ Tâche 2.1 + 2.4 (persistence + indices)
3. ✅ Tâche 3.1 (dashboard learning)
4. Reste selon besoins

### Métriques de succès

**Avant réparation:**
- Sécurité: 3/10 (secrets exposés, WS ouvert)
- Stabilité: 6/10 (bugs mineurs multiples)
- Fonctionnalités: 7/10 (learning incomplet)
- Performance: 6/10 (indices manquants)
- Tests: 0/10 (aucun test)

**Après Phase 4:**
- Sécurité: 9/10 (secrets gérés, auth WS, validation input)
- Stabilité: 9/10 (tous bugs corrigés, retry logic)
- Fonctionnalités: 10/10 (learning complet avec dashboard)
- Performance: 8/10 (indices, pooling, pagination)
- Tests: 8/10 (coverage > 70%)

**Note globale:** 7/10 → 9/10

---

**Prêt à commencer? Quelle phase souhaitez-vous prioriser?**
