"""
Durable Memory Module - AI Orchestrator v7
Mémoire persistante pour contexte serveur et décisions

Stocke:
- Services installés et leur état
- Conventions locales (ports, chemins, domaines)
- Incidents passés et résolutions
- Décisions techniques et leur justification
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings

logger = logging.getLogger(__name__)


class MemoryCategory(Enum):
    """Catégories de mémoire"""

    SERVICE = "service"  # Services installés
    CONVENTION = "convention"  # Conventions locales
    INCIDENT = "incident"  # Incidents passés
    DECISION = "decision"  # Décisions techniques
    CONTEXT = "context"  # Contexte général


@dataclass
class MemoryEntry:
    """Entrée de mémoire"""

    id: str
    category: MemoryCategory
    key: str
    value: Any
    description: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    confidence: float = 1.0  # 0.0 à 1.0
    expiry_date: Optional[datetime] = None  # CRQ-P0-5: TTL support


class DurableMemory:
    """Gestionnaire de mémoire durable"""

    def __init__(self, storage_path: str = "/home/lalpha/orchestrator-memory"):
        self.storage_path = storage_path
        self.memory_file = os.path.join(storage_path, "memory.json")
        self.entries: Dict[str, MemoryEntry] = {}
        self._ensure_storage()
        self._load()

    def _ensure_storage(self):
        """Crée le répertoire de stockage"""
        os.makedirs(self.storage_path, exist_ok=True)

    def _load(self):
        """Charge la mémoire depuis le fichier"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r") as f:
                    data = json.load(f)

                for entry_id, entry_data in data.items():
                    expiry = entry_data.get("expiry_date")
                    self.entries[entry_id] = MemoryEntry(
                        id=entry_id,
                        category=MemoryCategory(entry_data["category"]),
                        key=entry_data["key"],
                        value=entry_data["value"],
                        description=entry_data["description"],
                        created_at=datetime.fromisoformat(entry_data["created_at"]),
                        updated_at=datetime.fromisoformat(entry_data["updated_at"]),
                        tags=entry_data.get("tags", []),
                        confidence=entry_data.get("confidence", 1.0),
                        expiry_date=datetime.fromisoformat(expiry) if expiry else None,
                    )

                logger.info(f"[MEMORY] Chargé {len(self.entries)} entrées")
            except Exception as e:
                logger.error(f"[MEMORY] Erreur chargement: {e}")

    def _save(self):
        """Sauvegarde la mémoire dans le fichier"""
        try:
            data = {}
            for entry_id, entry in self.entries.items():
                data[entry_id] = {
                    "category": entry.category.value,
                    "key": entry.key,
                    "value": entry.value,
                    "description": entry.description,
                    "created_at": entry.created_at.isoformat(),
                    "updated_at": entry.updated_at.isoformat(),
                    "tags": entry.tags,
                    "confidence": entry.confidence,
                    "expiry_date": entry.expiry_date.isoformat() if entry.expiry_date else None,
                }

            with open(self.memory_file, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"[MEMORY] Sauvegardé {len(self.entries)} entrées")
        except Exception as e:
            logger.error(f"[MEMORY] Erreur sauvegarde: {e}")

    def _generate_id(self, category: MemoryCategory, key: str) -> str:
        """Génère un ID unique pour une entrée"""
        return f"{category.value}:{key}"

    def remember(
        self,
        category: MemoryCategory,
        key: str,
        value: Any,
        description: str,
        tags: List[str] = None,
        confidence: float = 1.0,
        ttl_days: Optional[int] = None,
    ) -> MemoryEntry:
        """
        Mémorise une information.

        Args:
            category: Catégorie de l'information
            key: Clé unique dans la catégorie
            value: Valeur à mémoriser
            description: Description humaine
            tags: Tags pour recherche
            confidence: Niveau de confiance (0.0-1.0)
            ttl_days: TTL en jours (défaut: MEMORY_TTL_DAYS si cleanup activé)

        Returns:
            Entrée de mémoire créée/mise à jour
        """
        entry_id = self._generate_id(category, key)

        # CRQ-P0-5: Quota enforcement AVANT création nouvelle entrée
        if entry_id not in self.entries:
            if (
                settings.ENABLE_MEMORY_CLEANUP
                and len(self.entries) >= settings.MEMORY_MAX_DOCUMENTS
            ):
                purge_count = max(1, int(len(self.entries) * 0.10))
                self._purge_oldest(purge_count)
                logger.warning(
                    f"[MEMORY] Quota atteint ({settings.MEMORY_MAX_DOCUMENTS}), "
                    f"purge de {purge_count} entrées"
                )

        # CRQ-P0-5: Calcul expiry_date
        expiry = None
        if settings.ENABLE_MEMORY_CLEANUP:
            days = ttl_days if ttl_days is not None else settings.MEMORY_TTL_DAYS
            expiry = datetime.now() + timedelta(days=days)

        if entry_id in self.entries:
            # Mise à jour
            entry = self.entries[entry_id]
            entry.value = value
            entry.description = description
            entry.updated_at = datetime.now()
            if tags:
                entry.tags = list(set(entry.tags + tags))
            entry.confidence = confidence
            # Reset TTL on update
            if expiry:
                entry.expiry_date = expiry
            logger.info(f"[MEMORY] Mis à jour: {entry_id}")
        else:
            # Nouvelle entrée
            entry = MemoryEntry(
                id=entry_id,
                category=category,
                key=key,
                value=value,
                description=description,
                tags=tags or [],
                confidence=confidence,
                expiry_date=expiry,
            )
            self.entries[entry_id] = entry
            logger.info(f"[MEMORY] Nouveau: {entry_id} (expiry: {expiry})")

        self._save()
        return entry

    def recall(
        self,
        category: Optional[MemoryCategory] = None,
        key: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_confidence: float = 0.0,
    ) -> List[MemoryEntry]:
        """
        Rappelle des informations de la mémoire.

        Args:
            category: Filtrer par catégorie
            key: Filtrer par clé exacte
            tags: Filtrer par tags (OR)
            min_confidence: Confiance minimale

        Returns:
            Liste des entrées correspondantes
        """
        results = []

        for entry in self.entries.values():
            # Filtre catégorie
            if category and entry.category != category:
                continue

            # Filtre clé
            if key and entry.key != key:
                continue

            # Filtre confiance
            if entry.confidence < min_confidence:
                continue

            # Filtre tags (OR)
            if tags:
                if not any(tag in entry.tags for tag in tags):
                    continue

            results.append(entry)

        # Trier par confiance décroissante
        results.sort(key=lambda e: e.confidence, reverse=True)

        return results

    def forget(self, category: MemoryCategory, key: str) -> bool:
        """
        Oublie une information.

        Args:
            category: Catégorie
            key: Clé

        Returns:
            True si supprimé, False sinon
        """
        entry_id = self._generate_id(category, key)

        if entry_id in self.entries:
            del self.entries[entry_id]
            self._save()
            logger.info(f"[MEMORY] Oublié: {entry_id}")
            return True

        return False

    def search(self, query: str) -> List[MemoryEntry]:
        """
        Recherche dans la mémoire par texte.

        Args:
            query: Texte à rechercher

        Returns:
            Entrées correspondantes
        """
        query_lower = query.lower()
        results = []

        for entry in self.entries.values():
            # Chercher dans key, description, tags, et value (si string)
            searchable = f"{entry.key} {entry.description} {' '.join(entry.tags)}"
            if isinstance(entry.value, str):
                searchable += f" {entry.value}"

            if query_lower in searchable.lower():
                results.append(entry)

        return results

    def get_context_summary(self) -> Dict:
        """
        Génère un résumé du contexte mémorisé.

        Returns:
            Résumé structuré
        """
        summary = {
            "total_entries": len(self.entries),
            "by_category": {},
            "recent_updates": [],
            "key_services": [],
            "key_conventions": [],
        }

        # Compter par catégorie
        for cat in MemoryCategory:
            entries = self.recall(category=cat)
            summary["by_category"][cat.value] = len(entries)

        # 5 dernières mises à jour
        recent = sorted(self.entries.values(), key=lambda e: e.updated_at, reverse=True)[:5]
        summary["recent_updates"] = [
            {"key": e.key, "category": e.category.value, "updated": e.updated_at.isoformat()}
            for e in recent
        ]

        # Services clés
        services = self.recall(category=MemoryCategory.SERVICE)
        summary["key_services"] = [
            {
                "name": s.key,
                "status": (
                    s.value.get("status", "unknown") if isinstance(s.value, dict) else "unknown"
                ),
            }
            for s in services[:10]
        ]

        # Conventions clés
        conventions = self.recall(category=MemoryCategory.CONVENTION)
        summary["key_conventions"] = [
            {"name": c.key, "value": str(c.value)[:50]} for c in conventions[:10]
        ]

        return summary

    def _purge_oldest(self, count: int):
        """
        Purge les N entrées les plus anciennes (CRQ-P0-5).

        Args:
            count: Nombre d'entrées à supprimer
        """
        if count <= 0 or len(self.entries) == 0:
            return

        # Trier par created_at croissant (plus anciennes en premier)
        sorted_entries = sorted(self.entries.values(), key=lambda e: e.created_at)

        # Supprimer les N plus anciennes
        for entry in sorted_entries[:count]:
            del self.entries[entry.id]
            logger.debug(f"[MEMORY] Purgé (quota): {entry.id}")

        self._save()

    def cleanup_expired(self) -> int:
        """
        Supprime les entrées expirées (TTL dépassé) - CRQ-P0-5.

        Returns:
            Nombre d'entrées supprimées
        """
        if not settings.ENABLE_MEMORY_CLEANUP:
            return 0

        now = datetime.now()
        expired_ids = []

        for entry in self.entries.values():
            if entry.expiry_date and now > entry.expiry_date:
                expired_ids.append(entry.id)

        for entry_id in expired_ids:
            del self.entries[entry_id]
            logger.debug(f"[MEMORY] Purgé (expiré): {entry_id}")

        if expired_ids:
            self._save()
            logger.info(f"[MEMORY] Cleanup: {len(expired_ids)} entrées expirées supprimées")

        return len(expired_ids)

    def initialize_server_context(self):
        """
        Initialise le contexte serveur avec les informations de base.
        Appelé au démarrage pour s'assurer que les infos essentielles sont présentes.
        """
        # Conventions de base
        base_conventions = [
            ("domain", "4lb.ca", "Domaine principal"),
            ("workspace", "/home/lalpha/orchestrator-workspace", "Répertoire de travail"),
            (
                "stack_dir",
                "/home/lalpha/projets/infrastructure/unified-stack",
                "Stack Docker principale",
            ),
            ("ai_tools_dir", "/home/lalpha/projets/ai-tools", "Projets IA"),
            ("ollama_models", "/mnt/ollama-models", "Modèles Ollama"),
            ("backup_dir", "/home/lalpha/backups", "Sauvegardes"),
        ]

        for key, value, desc in base_conventions:
            if not self.recall(category=MemoryCategory.CONVENTION, key=key):
                self.remember(MemoryCategory.CONVENTION, key, value, desc, tags=["base", "config"])

        # Services de base
        base_services = [
            ("ai-orchestrator", {"port": 8001, "type": "systemd"}, "Backend AI Orchestrator"),
            ("traefik", {"port": 443, "type": "docker"}, "Reverse proxy"),
            ("ollama", {"port": 11434, "type": "native"}, "LLM inference"),
            ("postgresql", {"port": 5432, "type": "docker"}, "Database + pgvector"),
        ]

        for key, value, desc in base_services:
            if not self.recall(category=MemoryCategory.SERVICE, key=key):
                self.remember(
                    MemoryCategory.SERVICE, key, value, desc, tags=["base", "infrastructure"]
                )

        logger.info("[MEMORY] Contexte serveur initialisé")


# Instance globale
durable_memory = DurableMemory()
