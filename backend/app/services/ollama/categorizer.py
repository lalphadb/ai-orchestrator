"""
Model Categorizer - Catégorise les modèles Ollama par usage
"""

import re
from typing import Any, Dict, List


class ModelCategory:
    """Catégories de modèles"""

    CODE = "code"
    CHAT = "chat"
    EMBEDDING = "embedding"
    VISION = "vision"
    INSTRUCT = "instruct"
    REASONING = "reasoning"
    UNKNOWN = "other"


# Patterns pour détection automatique
CATEGORY_PATTERNS = {
    ModelCategory.CODE: [
        r"coder",
        r"code",
        r"codestral",
        r"starcoder",
        r"wizardcoder",
    ],
    ModelCategory.EMBEDDING: [
        r"embed",
        r"nomic",
        r"mxbai",
        r"bge",
    ],
    ModelCategory.VISION: [
        r"vision",
        r"llava",
        r"bakllava",
        r"minicpm-v",
    ],
    ModelCategory.INSTRUCT: [
        r"-instruct",
        r":instruct",
    ],
    ModelCategory.REASONING: [
        r"deepseek-r1",
        r"o1",
        r"reasoning",
    ],
}

# Descriptions par catégorie
CATEGORY_INFO = {
    ModelCategory.CODE: {
        "name": "💻 Code",
        "description": "Spécialisés en programmation, debug, refactoring",
        "icon": "💻",
    },
    ModelCategory.CHAT: {
        "name": "💬 Chat",
        "description": "Conversation générale, assistance",
        "icon": "💬",
    },
    ModelCategory.EMBEDDING: {
        "name": "🔍 Embedding",
        "description": "Génération de vecteurs pour recherche sémantique",
        "icon": "🔍",
    },
    ModelCategory.VISION: {
        "name": "👁️ Vision",
        "description": "Analyse d'images et vision multimodale",
        "icon": "👁️",
    },
    ModelCategory.INSTRUCT: {
        "name": "📝 Instruct",
        "description": "Suivi d'instructions précises",
        "icon": "📝",
    },
    ModelCategory.REASONING: {
        "name": "🧠 Reasoning",
        "description": "Raisonnement complexe, mathématiques",
        "icon": "🧠",
    },
    ModelCategory.UNKNOWN: {
        "name": "🔹 Autres",
        "description": "Modèles génériques",
        "icon": "🔹",
    },
}


def categorize_model(model: Dict[str, Any]) -> str:
    """
    Catégorise un modèle Ollama par son nom et ses métadonnées

    Args:
        model: Dict avec 'name', 'details', etc.

    Returns:
        Catégorie (code, chat, embedding, etc.)
    """
    model_name = model.get("name", "").lower()
    details = model.get("details", {})
    family = details.get("family", "").lower() if details else ""

    # Check patterns par priorité
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, model_name, re.IGNORECASE):
                return category

    # Fallback sur la famille ou le nom
    if family in ["llama", "qwen", "gemma", "mistral", "phi"]:
        return ModelCategory.CHAT
    # Cloud / API models sans famille Ollama
    if any(p in model_name for p in ["kimi", "gemini"]):
        return ModelCategory.CHAT

    return ModelCategory.UNKNOWN


def categorize_models(models: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Catégorise une liste de modèles

    Args:
        models: Liste de dicts Ollama models

    Returns:
        Dict {category: [models]}
    """
    categorized = {cat: [] for cat in CATEGORY_INFO.keys()}

    for model in models:
        category = categorize_model(model)

        # Enrichir avec info catégorie
        model_enriched = {
            **model,
            "category": category,
            "category_info": CATEGORY_INFO.get(category, CATEGORY_INFO[ModelCategory.UNKNOWN]),
        }

        categorized[category].append(model_enriched)

    # Retirer catégories vides
    return {k: v for k, v in categorized.items() if v}


def get_model_badge(model: Dict[str, Any]) -> str:
    """Retourne un badge texte pour un modèle"""
    category = categorize_model(model)
    info = CATEGORY_INFO.get(category, CATEGORY_INFO[ModelCategory.UNKNOWN])

    details = model.get("details", {})
    size = details.get("parameter_size", "?")
    quant = details.get("quantization_level", "")

    badges = [info["icon"], size]
    if quant:
        badges.append(quant)

    return " ".join(badges)


def get_recommended_models_by_task(models: List[Dict[str, Any]], task: str) -> List[str]:
    """
    Recommande des modèles selon la tâche

    Args:
        models: Liste de modèles disponibles
        task: "code", "chat", "embed", etc.

    Returns:
        Liste de noms de modèles recommandés
    """
    categorized = categorize_models(models)

    task_to_category = {
        "code": ModelCategory.CODE,
        "programming": ModelCategory.CODE,
        "debug": ModelCategory.CODE,
        "chat": ModelCategory.CHAT,
        "conversation": ModelCategory.CHAT,
        "embed": ModelCategory.EMBEDDING,
        "search": ModelCategory.EMBEDDING,
        "vision": ModelCategory.VISION,
        "image": ModelCategory.VISION,
        "instruct": ModelCategory.INSTRUCT,
        "reasoning": ModelCategory.REASONING,
        "math": ModelCategory.REASONING,
    }

    category = task_to_category.get(task.lower(), ModelCategory.CHAT)
    recommended = categorized.get(category, [])

    # Trier par taille de paramètres (plus gros = meilleur généralement)
    def get_size(m):
        try:
            size_str = m.get("details", {}).get("parameter_size", "0B")
            # Convertir "8.0B" en float
            return float(size_str.replace("B", "").replace("M", "e-3"))
        except (ValueError, AttributeError, TypeError):
            return 0

    recommended.sort(key=get_size, reverse=True)

    return [m["name"] for m in recommended[:5]]
