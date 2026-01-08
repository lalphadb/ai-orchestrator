"""
LearningMemory - Mémoire d'apprentissage basée sur ChromaDB

Stocke et récupère les expériences pour améliorer les réponses:
- Commandes réussies avec leur contexte
- Erreurs et leurs corrections
- Patterns de résolution de problèmes
- Préférences utilisateur
"""

import chromadb
from chromadb.config import Settings
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class LearningMemory:
    """Mémoire d'apprentissage persistante avec ChromaDB."""
    
    def __init__(self, chroma_host: str = "localhost", chroma_port: int = 8000):
        """
        Initialise la connexion à ChromaDB.
        
        Args:
            chroma_host: Hôte ChromaDB
            chroma_port: Port ChromaDB
        """
        try:
            self.client = chromadb.HttpClient(
                host=chroma_host,
                port=chroma_port,
                settings=Settings(anonymized_telemetry=False)
            )
            self._init_collections()
            logger.info(f"LearningMemory connecté à ChromaDB {chroma_host}:{chroma_port}")
        except Exception as e:
            logger.error(f"Erreur connexion ChromaDB: {e}")
            self.client = None
    
    def _init_collections(self):
        """Initialise les collections ChromaDB."""
        # Collection des expériences (succès/échecs)
        self.experiences = self.client.get_or_create_collection(
            name="ai_experiences",
            metadata={"description": "Expériences d'exécution (succès/échecs)"}
        )
        
        # Collection des patterns de résolution
        self.patterns = self.client.get_or_create_collection(
            name="ai_patterns",
            metadata={"description": "Patterns de résolution de problèmes"}
        )
        
        # Collection des corrections d'erreurs
        self.corrections = self.client.get_or_create_collection(
            name="ai_corrections",
            metadata={"description": "Erreurs et leurs corrections"}
        )
        
        # Collection des préférences/contexte utilisateur
        self.user_context = self.client.get_or_create_collection(
            name="ai_user_context",
            metadata={"description": "Contexte et préférences utilisateur"}
        )
        
        logger.info("Collections ChromaDB initialisées")
    
    def _generate_id(self, content: str) -> str:
        """Génère un ID unique basé sur le contenu."""
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    # ==================== EXPÉRIENCES ====================
    
    def store_experience(
        self,
        query: str,
        response: str,
        tools_used: List[str],
        success: bool,
        duration_ms: int,
        iterations: int,
        error: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """
        Stocke une expérience d'exécution.
        
        Args:
            query: Question/demande originale
            response: Réponse générée
            tools_used: Liste des outils utilisés
            success: Si l'exécution a réussi
            duration_ms: Durée en millisecondes
            iterations: Nombre d'itérations ReAct
            error: Message d'erreur si échec
            user_id: ID utilisateur optionnel
            
        Returns:
            ID de l'expérience stockée
        """
        if not self.client:
            return None
            
        exp_id = self._generate_id(f"{query}{datetime.now().isoformat()}")
        
        # Document texte pour la recherche sémantique
        document = f"Query: {query}\nTools: {', '.join(tools_used)}\nSuccess: {success}"
        if error:
            document += f"\nError: {error}"
        
        # Métadonnées structurées
        metadata = {
            "query": query[:500],  # Limite pour ChromaDB
            "success": success,
            "tools_used": json.dumps(tools_used),
            "duration_ms": duration_ms,
            "iterations": iterations,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id or "anonymous",
            "score": 1.0 if success else 0.0  # Score initial
        }
        
        if error:
            metadata["error"] = error[:500]
        
        try:
            self.experiences.add(
                ids=[exp_id],
                documents=[document],
                metadatas=[metadata]
            )
            logger.info(f"Expérience stockée: {exp_id} (success={success})")
            return exp_id
        except Exception as e:
            logger.error(f"Erreur stockage expérience: {e}")
            return None
    
    def get_similar_experiences(
        self,
        query: str,
        n_results: int = 5,
        success_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Récupère les expériences similaires pour enrichir le contexte.
        
        Args:
            query: Question actuelle
            n_results: Nombre de résultats
            success_only: Ne retourner que les succès
            
        Returns:
            Liste des expériences similaires avec leur score
        """
        if not self.client:
            return []
        
        try:
            # Recherche sémantique
            where_filter = {"success": True} if success_only else None
            
            results = self.experiences.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter
            )
            
            experiences = []
            if results and results['metadatas']:
                for i, metadata in enumerate(results['metadatas'][0]):
                    exp = {
                        "id": results['ids'][0][i],
                        "query": metadata.get('query', ''),
                        "tools_used": json.loads(metadata.get('tools_used', '[]')),
                        "success": metadata.get('success', False),
                        "score": metadata.get('score', 0.0),
                        "distance": results['distances'][0][i] if results['distances'] else 0,
                        "relevance": 1 - (results['distances'][0][i] if results['distances'] else 0)
                    }
                    experiences.append(exp)
            
            return experiences
            
        except Exception as e:
            logger.error(f"Erreur recherche expériences: {e}")
            return []
    
    # ==================== PATTERNS ====================
    
    def store_pattern(
        self,
        problem_type: str,
        solution_steps: List[str],
        tools_sequence: List[str],
        success_rate: float,
        examples: List[str]
    ) -> str:
        """
        Stocke un pattern de résolution réussi.
        
        Args:
            problem_type: Type de problème (ex: "docker_debug", "file_search")
            solution_steps: Étapes de résolution
            tools_sequence: Séquence d'outils utilisés
            success_rate: Taux de succès du pattern
            examples: Exemples de requêtes résolues
            
        Returns:
            ID du pattern
        """
        if not self.client:
            return None
            
        pattern_id = self._generate_id(f"{problem_type}{json.dumps(tools_sequence)}")
        
        document = f"Problem: {problem_type}\nSteps: {'; '.join(solution_steps)}\nTools: {', '.join(tools_sequence)}"
        
        metadata = {
            "problem_type": problem_type,
            "solution_steps": json.dumps(solution_steps),
            "tools_sequence": json.dumps(tools_sequence),
            "success_rate": success_rate,
            "examples": json.dumps(examples[:5]),  # Max 5 exemples
            "usage_count": 1,
            "last_used": datetime.now().isoformat()
        }
        
        try:
            # Vérifier si le pattern existe déjà
            existing = self.patterns.get(ids=[pattern_id])
            if existing and existing['ids']:
                # Mettre à jour le compteur
                old_meta = existing['metadatas'][0]
                metadata['usage_count'] = old_meta.get('usage_count', 0) + 1
                self.patterns.update(
                    ids=[pattern_id],
                    metadatas=[metadata]
                )
            else:
                self.patterns.add(
                    ids=[pattern_id],
                    documents=[document],
                    metadatas=[metadata]
                )
            
            logger.info(f"Pattern stocké/mis à jour: {problem_type}")
            return pattern_id
            
        except Exception as e:
            logger.error(f"Erreur stockage pattern: {e}")
            return None
    
    def get_relevant_patterns(
        self,
        query: str,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Récupère les patterns pertinents pour la requête.
        
        Args:
            query: Question actuelle
            n_results: Nombre de résultats
            
        Returns:
            Liste des patterns avec leurs métadonnées
        """
        if not self.client:
            return []
        
        try:
            results = self.patterns.query(
                query_texts=[query],
                n_results=n_results
            )
            
            patterns = []
            if results and results['metadatas']:
                for i, metadata in enumerate(results['metadatas'][0]):
                    pattern = {
                        "problem_type": metadata.get('problem_type', ''),
                        "solution_steps": json.loads(metadata.get('solution_steps', '[]')),
                        "tools_sequence": json.loads(metadata.get('tools_sequence', '[]')),
                        "success_rate": metadata.get('success_rate', 0.0),
                        "usage_count": metadata.get('usage_count', 0),
                        "relevance": 1 - (results['distances'][0][i] if results['distances'] else 0)
                    }
                    patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Erreur recherche patterns: {e}")
            return []
    
    # ==================== CORRECTIONS ====================
    
    def store_correction(
        self,
        error_type: str,
        error_message: str,
        failed_approach: str,
        successful_correction: str,
        context: str
    ) -> str:
        """
        Stocke une correction d'erreur pour apprentissage.
        
        Args:
            error_type: Type d'erreur (ex: "command_not_found", "permission_denied")
            error_message: Message d'erreur original
            failed_approach: Approche qui a échoué
            successful_correction: Correction qui a fonctionné
            context: Contexte de l'erreur
            
        Returns:
            ID de la correction
        """
        if not self.client:
            return None
            
        corr_id = self._generate_id(f"{error_type}{error_message[:100]}")
        
        document = f"Error: {error_type}\nMessage: {error_message}\nFailed: {failed_approach}\nCorrection: {successful_correction}"
        
        metadata = {
            "error_type": error_type,
            "error_message": error_message[:500],
            "failed_approach": failed_approach[:500],
            "successful_correction": successful_correction[:1000],
            "context": context[:500],
            "timestamp": datetime.now().isoformat(),
            "times_used": 1
        }
        
        try:
            self.corrections.add(
                ids=[corr_id],
                documents=[document],
                metadatas=[metadata]
            )
            logger.info(f"Correction stockée: {error_type}")
            return corr_id
        except Exception as e:
            logger.error(f"Erreur stockage correction: {e}")
            return None
    
    def get_correction_for_error(
        self,
        error_message: str,
        context: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Trouve une correction pour une erreur similaire.
        
        Args:
            error_message: Message d'erreur
            context: Contexte optionnel
            
        Returns:
            Correction trouvée ou None
        """
        if not self.client:
            return None
        
        try:
            query = f"{error_message} {context}"
            results = self.corrections.query(
                query_texts=[query],
                n_results=1
            )
            
            if results and results['metadatas'] and results['metadatas'][0]:
                metadata = results['metadatas'][0][0]
                distance = results['distances'][0][0] if results['distances'] else 1
                
                # Seulement si la correspondance est bonne (distance < 0.5)
                if distance < 0.5:
                    return {
                        "error_type": metadata.get('error_type', ''),
                        "successful_correction": metadata.get('successful_correction', ''),
                        "context": metadata.get('context', ''),
                        "relevance": 1 - distance
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur recherche correction: {e}")
            return None
    
    # ==================== CONTEXTE UTILISATEUR ====================
    
    def store_user_preference(
        self,
        user_id: str,
        preference_type: str,
        preference_value: str,
        context: str = ""
    ):
        """Stocke une préférence utilisateur."""
        if not self.client:
            return
            
        pref_id = self._generate_id(f"{user_id}{preference_type}")
        
        document = f"User preference: {preference_type} = {preference_value}"
        
        metadata = {
            "user_id": user_id,
            "preference_type": preference_type,
            "preference_value": preference_value,
            "context": context,
            "updated_at": datetime.now().isoformat()
        }
        
        try:
            # Upsert
            existing = self.user_context.get(ids=[pref_id])
            if existing and existing['ids']:
                self.user_context.update(
                    ids=[pref_id],
                    documents=[document],
                    metadatas=[metadata]
                )
            else:
                self.user_context.add(
                    ids=[pref_id],
                    documents=[document],
                    metadatas=[metadata]
                )
        except Exception as e:
            logger.error(f"Erreur stockage préférence: {e}")
    
    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Récupère le contexte utilisateur."""
        if not self.client:
            return {}
        
        try:
            results = self.user_context.get(
                where={"user_id": user_id}
            )
            
            context = {}
            if results and results['metadatas']:
                for metadata in results['metadatas']:
                    pref_type = metadata.get('preference_type', '')
                    pref_value = metadata.get('preference_value', '')
                    if pref_type:
                        context[pref_type] = pref_value
            
            return context
            
        except Exception as e:
            logger.error(f"Erreur récupération contexte: {e}")
            return {}
    
    # ==================== STATS ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de la mémoire."""
        if not self.client:
            return {"status": "disconnected"}
        
        try:
            return {
                "status": "connected",
                "experiences_count": self.experiences.count(),
                "patterns_count": self.patterns.count(),
                "corrections_count": self.corrections.count(),
                "user_contexts_count": self.user_context.count()
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def update_experience_score(self, exp_id: str, score_delta: float):
        """Met à jour le score d'une expérience (feedback)."""
        if not self.client:
            return
        
        try:
            existing = self.experiences.get(ids=[exp_id])
            if existing and existing['metadatas']:
                metadata = existing['metadatas'][0]
                new_score = max(0, min(1, metadata.get('score', 0.5) + score_delta))
                metadata['score'] = new_score
                self.experiences.update(ids=[exp_id], metadatas=[metadata])
                logger.info(f"Score mis à jour: {exp_id} -> {new_score}")
        except Exception as e:
            logger.error(f"Erreur mise à jour score: {e}")


# Instance singleton
_learning_memory: Optional[LearningMemory] = None

def get_learning_memory() -> LearningMemory:
    """Retourne l'instance singleton de LearningMemory."""
    global _learning_memory
    if _learning_memory is None:
        _learning_memory = LearningMemory()
    return _learning_memory
