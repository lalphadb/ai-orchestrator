"""
ContextEnricher - Enrichit les prompts avec le contexte appris

Injecte dans le prompt LLM:
- Expériences similaires réussies
- Patterns de résolution
- Corrections d'erreurs connues
- Contexte utilisateur
"""

from typing import List, Dict, Any, Optional
import logging

from .memory import LearningMemory, get_learning_memory

logger = logging.getLogger(__name__)


class ContextEnricher:
    """Enrichit les prompts avec le contexte de la mémoire d'apprentissage."""
    
    def __init__(self, memory: Optional[LearningMemory] = None):
        """
        Initialise l'enrichisseur.
        
        Args:
            memory: Instance LearningMemory (ou utilise le singleton)
        """
        self.memory = memory or get_learning_memory()
    
    def enrich_prompt(
        self,
        query: str,
        user_id: Optional[str] = None,
        include_experiences: bool = True,
        include_patterns: bool = True,
        include_corrections: bool = True,
        max_experiences: int = 3,
        max_patterns: int = 2
    ) -> str:
        """
        Génère un contexte enrichi à ajouter au prompt.
        
        Args:
            query: Question de l'utilisateur
            user_id: ID utilisateur pour le contexte personnalisé
            include_experiences: Inclure les expériences similaires
            include_patterns: Inclure les patterns de résolution
            include_corrections: Inclure les corrections d'erreurs
            max_experiences: Nombre max d'expériences
            max_patterns: Nombre max de patterns
            
        Returns:
            Contexte enrichi à injecter dans le prompt
        """
        context_parts = []
        
        # 1. Expériences similaires réussies
        if include_experiences:
            experiences = self.memory.get_similar_experiences(
                query, 
                n_results=max_experiences,
                success_only=True
            )
            
            if experiences:
                exp_context = self._format_experiences(experiences)
                if exp_context:
                    context_parts.append(exp_context)
        
        # 2. Patterns de résolution
        if include_patterns:
            patterns = self.memory.get_relevant_patterns(
                query,
                n_results=max_patterns
            )
            
            if patterns:
                pattern_context = self._format_patterns(patterns)
                if pattern_context:
                    context_parts.append(pattern_context)
        
        # 3. Contexte utilisateur
        if user_id:
            user_context = self.memory.get_user_context(user_id)
            if user_context:
                user_ctx = self._format_user_context(user_context)
                if user_ctx:
                    context_parts.append(user_ctx)
        
        if not context_parts:
            return ""
        
        # Assembler le contexte
        full_context = "\n\n".join(context_parts)
        
        return f"""
<learned_context>
Based on previous successful interactions, here is relevant context:

{full_context}

Use this context to improve your response, but don't mention it explicitly.
</learned_context>
"""
    
    def _format_experiences(self, experiences: List[Dict[str, Any]]) -> str:
        """Formate les expériences pour le prompt."""
        if not experiences:
            return ""
        
        # Ne garder que les plus pertinentes (relevance > 0.5)
        relevant = [e for e in experiences if e.get('relevance', 0) > 0.5]
        if not relevant:
            return ""
        
        lines = ["## Similar Successful Queries:"]
        
        for exp in relevant[:3]:
            tools = ", ".join(exp.get('tools_used', []))
            lines.append(f"- Query: \"{exp['query'][:100]}...\"")
            if tools:
                lines.append(f"  Tools used: {tools}")
        
        return "\n".join(lines)
    
    def _format_patterns(self, patterns: List[Dict[str, Any]]) -> str:
        """Formate les patterns pour le prompt."""
        if not patterns:
            return ""
        
        # Ne garder que les patterns avec bon taux de succès
        good_patterns = [
            p for p in patterns 
            if p.get('success_rate', 0) >= 0.7 and p.get('relevance', 0) > 0.4
        ]
        
        if not good_patterns:
            return ""
        
        lines = ["## Recommended Approaches:"]
        
        for p in good_patterns[:2]:
            lines.append(f"- For {p['problem_type']} problems:")
            tools = " → ".join(p.get('tools_sequence', []))
            if tools:
                lines.append(f"  Suggested tool sequence: {tools}")
            lines.append(f"  Success rate: {p['success_rate']:.0%}")
        
        return "\n".join(lines)
    
    def _format_user_context(self, context: Dict[str, Any]) -> str:
        """Formate le contexte utilisateur pour le prompt."""
        if not context:
            return ""
        
        lines = ["## User Preferences:"]
        
        for key, value in context.items():
            # Traduire les clés en descriptions lisibles
            key_labels = {
                "preferred_model": "Preferred model",
                "verbose_output": "Prefers detailed output",
                "coding_style": "Coding style preference",
                "language": "Preferred language"
            }
            label = key_labels.get(key, key.replace("_", " ").title())
            lines.append(f"- {label}: {value}")
        
        return "\n".join(lines)
    
    def get_correction_hint(self, error_message: str, context: str = "") -> Optional[str]:
        """
        Obtient un indice de correction pour une erreur.
        
        Args:
            error_message: Message d'erreur
            context: Contexte de l'erreur
            
        Returns:
            Indice de correction ou None
        """
        correction = self.memory.get_correction_for_error(error_message, context)
        
        if correction and correction.get('relevance', 0) > 0.6:
            return f"""
<error_correction_hint>
A similar error was encountered before and resolved:
- Error type: {correction['error_type']}
- Successful correction: {correction['successful_correction']}

Try applying a similar approach.
</error_correction_hint>
"""
        
        return None


# Instance singleton
_context_enricher: Optional[ContextEnricher] = None

def get_context_enricher() -> ContextEnricher:
    """Retourne l'instance singleton."""
    global _context_enricher
    if _context_enricher is None:
        _context_enricher = ContextEnricher()
    return _context_enricher
