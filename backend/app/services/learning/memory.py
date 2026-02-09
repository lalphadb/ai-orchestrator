"""
LearningMemory - Memoire d'apprentissage basee sur PostgreSQL + pgvector

Stocke et recupere les experiences pour ameliorer les reponses:
- Commandes reussies avec leur contexte
- Erreurs et leurs corrections
- Patterns de resolution de problemes
- Preferences utilisateur
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import LearningMemory as LearningMemoryModel
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

# Ollama embedding endpoint
OLLAMA_EMBED_URL = f"{settings.OLLAMA_URL}/api/embeddings"
EMBED_MODEL = "bge-m3"


def _generate_embedding(content: str) -> Optional[List[float]]:
    """Generate embedding via Ollama bge-m3 (synchronous)."""
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(OLLAMA_EMBED_URL, json={"model": EMBED_MODEL, "prompt": content})
            if resp.status_code == 200:
                return resp.json().get("embedding", [])
    except Exception as e:
        logger.warning(f"Embedding generation failed: {e}")
    return None


class LearningMemory:
    """Memoire d'apprentissage persistante avec PostgreSQL + pgvector."""

    def __init__(self):
        """Initialise la connexion PostgreSQL."""
        self.connected = False
        try:
            # Test connection
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            self.connected = True
            logger.info("LearningMemory connected to PostgreSQL")
        except Exception as e:
            logger.error(f"LearningMemory: PostgreSQL connection failed: {e}")

    def _get_db(self) -> Session:
        """Get a new database session."""
        return SessionLocal()

    def reconnect(self) -> bool:
        """Force reconnection test."""
        try:
            db = self._get_db()
            db.execute(text("SELECT 1"))
            db.close()
            self.connected = True
            return True
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            self.connected = False
            return False

    def _generate_id(self, content: str) -> str:
        """Generate a unique ID based on content."""
        return hashlib.md5(content.encode()).hexdigest()[:16]

    # ==================== EXPERIENCES ====================

    def store_experience(
        self,
        query: str,
        response: str,
        tools_used: List[str],
        success: bool,
        duration_ms: int,
        iterations: int,
        error: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[str]:
        """Stocke une experience d'execution."""
        if not self.connected:
            return None

        exp_id = self._generate_id(f"{query}{datetime.now(timezone.utc).isoformat()}")
        document = f"Query: {query}\nTools: {', '.join(tools_used)}\nSuccess: {success}"
        if error:
            document += f"\nError: {error}"

        metadata = {
            "query": query[:500],
            "success": success,
            "tools_used": tools_used,
            "duration_ms": duration_ms,
            "iterations": iterations,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id or "anonymous",
            "score": 1.0 if success else 0.0,
        }
        if error:
            metadata["error"] = error[:500]

        db = self._get_db()
        try:
            embedding = _generate_embedding(document)
            entry = LearningMemoryModel(
                id=exp_id,
                collection="ai_experiences",
                content=document,
                metadata_=json.dumps(metadata),
                embedding=embedding,
            )
            db.add(entry)
            db.commit()
            logger.info(f"Experience stored: {exp_id} (success={success})")
            return exp_id
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing experience: {e}")
            return None
        finally:
            db.close()

    def get_similar_experiences(
        self, query: str, n_results: int = 5, success_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Recupere les experiences similaires via recherche vectorielle."""
        if not self.connected:
            return []

        db = self._get_db()
        try:
            embedding = _generate_embedding(query)
            if not embedding:
                return []

            # pgvector cosine distance search
            sql = text(
                """
                SELECT id, content, metadata, embedding <=> :emb AS distance
                FROM learning_memories
                WHERE collection = 'ai_experiences'
                ORDER BY embedding <=> :emb
                LIMIT :limit
            """
            )
            rows = db.execute(sql, {"emb": str(embedding), "limit": n_results}).fetchall()

            experiences = []
            for row in rows:
                meta = json.loads(row.metadata) if row.metadata else {}
                if success_only and not meta.get("success", False):
                    continue
                experiences.append(
                    {
                        "id": row.id,
                        "query": meta.get("query", ""),
                        "tools_used": meta.get("tools_used", []),
                        "success": meta.get("success", False),
                        "score": meta.get("score", 0.0),
                        "distance": row.distance,
                        "relevance": 1 - row.distance if row.distance else 0,
                    }
                )

            return experiences

        except Exception as e:
            logger.error(f"Error searching experiences: {e}")
            return []
        finally:
            db.close()

    # ==================== PATTERNS ====================

    def store_pattern(
        self,
        problem_type: str,
        solution_steps: List[str],
        tools_sequence: List[str],
        success_rate: float,
        examples: List[str],
    ) -> Optional[str]:
        """Stocke un pattern de resolution reussi."""
        if not self.connected:
            return None

        pattern_id = self._generate_id(f"{problem_type}{json.dumps(tools_sequence)}")
        document = f"Problem: {problem_type}\nSteps: {'; '.join(solution_steps)}\nTools: {', '.join(tools_sequence)}"

        metadata = {
            "problem_type": problem_type,
            "solution_steps": solution_steps,
            "tools_sequence": tools_sequence,
            "success_rate": success_rate,
            "examples": examples[:5],
            "usage_count": 1,
            "last_used": datetime.now(timezone.utc).isoformat(),
        }

        db = self._get_db()
        try:
            existing = db.query(LearningMemoryModel).filter_by(id=pattern_id).first()
            if existing:
                old_meta = json.loads(existing.metadata_) if existing.metadata_ else {}
                metadata["usage_count"] = old_meta.get("usage_count", 0) + 1
                existing.metadata_ = json.dumps(metadata)
                existing.updated_at = datetime.now(timezone.utc)
            else:
                embedding = _generate_embedding(document)
                entry = LearningMemoryModel(
                    id=pattern_id,
                    collection="ai_patterns",
                    content=document,
                    metadata_=json.dumps(metadata),
                    embedding=embedding,
                )
                db.add(entry)

            db.commit()
            logger.info(f"Pattern stored/updated: {problem_type}")
            return pattern_id
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing pattern: {e}")
            return None
        finally:
            db.close()

    def get_relevant_patterns(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Recupere les patterns pertinents via recherche vectorielle."""
        if not self.connected:
            return []

        db = self._get_db()
        try:
            embedding = _generate_embedding(query)
            if not embedding:
                return []

            sql = text(
                """
                SELECT id, content, metadata, embedding <=> :emb AS distance
                FROM learning_memories
                WHERE collection = 'ai_patterns'
                ORDER BY embedding <=> :emb
                LIMIT :limit
            """
            )
            rows = db.execute(sql, {"emb": str(embedding), "limit": n_results}).fetchall()

            patterns = []
            for row in rows:
                meta = json.loads(row.metadata) if row.metadata else {}
                patterns.append(
                    {
                        "problem_type": meta.get("problem_type", ""),
                        "solution_steps": meta.get("solution_steps", []),
                        "tools_sequence": meta.get("tools_sequence", []),
                        "success_rate": meta.get("success_rate", 0.0),
                        "usage_count": meta.get("usage_count", 0),
                        "relevance": 1 - row.distance if row.distance else 0,
                    }
                )

            return patterns
        except Exception as e:
            logger.error(f"Error searching patterns: {e}")
            return []
        finally:
            db.close()

    def get_top_patterns(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Recupere les patterns les plus utilises."""
        if not self.connected:
            return []

        db = self._get_db()
        try:
            rows = db.query(LearningMemoryModel).filter_by(collection="ai_patterns").all()

            patterns = []
            for row in rows:
                meta = json.loads(row.metadata_) if row.metadata_ else {}
                patterns.append(
                    {
                        "pattern": row.content,
                        "problem_type": meta.get("problem_type", ""),
                        "solution_steps": meta.get("solution_steps", []),
                        "tools_sequence": meta.get("tools_sequence", []),
                        "success_rate": meta.get("success_rate", 0.0),
                        "usage_count": meta.get("usage_count", 0),
                        "created_at": row.created_at.isoformat() if row.created_at else "",
                    }
                )

            patterns.sort(key=lambda x: x["usage_count"], reverse=True)
            return patterns[:limit]
        except Exception as e:
            logger.error(f"Error get_top_patterns: {e}")
            return []
        finally:
            db.close()

    # ==================== CORRECTIONS ====================

    def store_correction(
        self,
        error_type: str,
        error_message: str,
        failed_approach: str,
        successful_correction: str,
        context: str,
    ) -> Optional[str]:
        """Stocke une correction d'erreur pour apprentissage."""
        if not self.connected:
            return None

        corr_id = self._generate_id(f"{error_type}{error_message[:100]}")
        document = f"Error: {error_type}\nMessage: {error_message}\nFailed: {failed_approach}\nCorrection: {successful_correction}"

        metadata = {
            "error_type": error_type,
            "error_message": error_message[:500],
            "failed_approach": failed_approach[:500],
            "successful_correction": successful_correction[:1000],
            "context": context[:500],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "times_used": 1,
        }

        db = self._get_db()
        try:
            embedding = _generate_embedding(document)
            entry = LearningMemoryModel(
                id=corr_id,
                collection="ai_corrections",
                content=document,
                metadata_=json.dumps(metadata),
                embedding=embedding,
            )
            db.add(entry)
            db.commit()
            logger.info(f"Correction stored: {error_type}")
            return corr_id
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing correction: {e}")
            return None
        finally:
            db.close()

    def get_correction_for_error(
        self, error_message: str, context: str = ""
    ) -> Optional[Dict[str, Any]]:
        """Trouve une correction pour une erreur similaire via recherche vectorielle."""
        if not self.connected:
            return None

        db = self._get_db()
        try:
            query_text = f"{error_message} {context}"
            embedding = _generate_embedding(query_text)
            if not embedding:
                return None

            sql = text(
                """
                SELECT id, metadata, embedding <=> :emb AS distance
                FROM learning_memories
                WHERE collection = 'ai_corrections'
                ORDER BY embedding <=> :emb
                LIMIT 1
            """
            )
            row = db.execute(sql, {"emb": str(embedding)}).fetchone()

            if row and row.distance < 0.5:
                meta = json.loads(row.metadata) if row.metadata else {}
                return {
                    "error_type": meta.get("error_type", ""),
                    "successful_correction": meta.get("successful_correction", ""),
                    "context": meta.get("context", ""),
                    "relevance": 1 - row.distance,
                }

            return None
        except Exception as e:
            logger.error(f"Error searching correction: {e}")
            return None
        finally:
            db.close()

    # ==================== CONTEXTE UTILISATEUR ====================

    def store_user_preference(
        self, user_id: str, preference_type: str, preference_value: str, context: str = ""
    ):
        """Stocke une preference utilisateur."""
        if not self.connected:
            return

        pref_id = self._generate_id(f"{user_id}{preference_type}")
        document = f"User preference: {preference_type} = {preference_value}"

        metadata = {
            "user_id": user_id,
            "preference_type": preference_type,
            "preference_value": preference_value,
            "context": context,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        db = self._get_db()
        try:
            existing = db.query(LearningMemoryModel).filter_by(id=pref_id).first()
            if existing:
                existing.content = document
                existing.metadata_ = json.dumps(metadata)
                existing.updated_at = datetime.now(timezone.utc)
            else:
                entry = LearningMemoryModel(
                    id=pref_id,
                    collection="ai_user_context",
                    content=document,
                    metadata_=json.dumps(metadata),
                )
                db.add(entry)

            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing preference: {e}")
        finally:
            db.close()

    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Recupere le contexte utilisateur."""
        if not self.connected:
            return {}

        db = self._get_db()
        try:
            rows = db.query(LearningMemoryModel).filter_by(collection="ai_user_context").all()

            context = {}
            for row in rows:
                meta = json.loads(row.metadata_) if row.metadata_ else {}
                if meta.get("user_id") == user_id:
                    pref_type = meta.get("preference_type", "")
                    pref_value = meta.get("preference_value", "")
                    if pref_type:
                        context[pref_type] = pref_value

            return context
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return {}
        finally:
            db.close()

    # ==================== STATS ====================

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de la memoire."""
        if not self.connected:
            return {"status": "disconnected"}

        db = self._get_db()
        try:

            def _count(collection: str) -> int:
                return db.query(LearningMemoryModel).filter_by(collection=collection).count()

            return {
                "status": "connected",
                "experiences_count": _count("ai_experiences"),
                "patterns_count": _count("ai_patterns"),
                "corrections_count": _count("ai_corrections"),
                "user_contexts_count": _count("ai_user_context"),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
        finally:
            db.close()

    def update_experience_score(self, exp_id: str, score_delta: float):
        """Met a jour le score d'une experience (feedback)."""
        if not self.connected:
            return

        db = self._get_db()
        try:
            entry = db.query(LearningMemoryModel).filter_by(id=exp_id).first()
            if entry and entry.metadata_:
                meta = json.loads(entry.metadata_)
                new_score = max(0, min(1, meta.get("score", 0.5) + score_delta))
                meta["score"] = new_score
                entry.metadata_ = json.dumps(meta)
                db.commit()
                logger.info(f"Score updated: {exp_id} -> {new_score}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating score: {e}")
        finally:
            db.close()


# Instance singleton
_learning_memory: Optional[LearningMemory] = None


def get_learning_memory() -> LearningMemory:
    """Retourne l'instance singleton de LearningMemory."""
    global _learning_memory
    if _learning_memory is None:
        _learning_memory = LearningMemory()
    return _learning_memory
