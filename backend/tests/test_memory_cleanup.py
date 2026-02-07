"""
Tests pour CRQ-P0-5: Memory Cleanup (TTL + Quota)
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from app.core.config import settings
from app.services.react_engine.memory import DurableMemory, MemoryCategory


class TestMemoryTTL:
    """Tests pour TTL (Time-To-Live) des memories"""

    def test_memory_with_ttl_enabled(self, monkeypatch):
        """Avec ENABLE_MEMORY_CLEANUP=true, les memories doivent avoir une expiry_date"""
        monkeypatch.setattr(settings, "ENABLE_MEMORY_CLEANUP", True)
        monkeypatch.setattr(settings, "MEMORY_TTL_DAYS", 7)

        memory = DurableMemory(storage_path="/tmp/test_memory_ttl")
        entry = memory.remember(
            MemoryCategory.CONTEXT, "test_key", "test_value", "Test TTL", ttl_days=7
        )

        assert entry.expiry_date is not None
        expected_expiry = datetime.now() + timedelta(days=7)
        # Tolérance 10 secondes pour le test
        assert abs((entry.expiry_date - expected_expiry).total_seconds()) < 10

    def test_memory_without_ttl_disabled(self, monkeypatch):
        """Avec ENABLE_MEMORY_CLEANUP=false, les memories ne doivent PAS avoir d'expiry_date"""
        monkeypatch.setattr(settings, "ENABLE_MEMORY_CLEANUP", False)

        memory = DurableMemory(storage_path="/tmp/test_memory_no_ttl")
        entry = memory.remember(MemoryCategory.CONTEXT, "test_key", "test_value", "No TTL")

        assert entry.expiry_date is None

    def test_cleanup_expired_memories(self, monkeypatch):
        """cleanup_expired() doit supprimer les entrées dont le TTL est dépassé"""
        monkeypatch.setattr(settings, "ENABLE_MEMORY_CLEANUP", True)

        memory = DurableMemory(storage_path="/tmp/test_cleanup_expired")

        # Créer une entrée avec TTL dépassé (expiry_date dans le passé)
        past_entry = memory.remember(
            MemoryCategory.CONTEXT, "expired_key", "expired", "Expired entry"
        )
        # Forcer l'expiry_date dans le passé
        past_entry.expiry_date = datetime.now() - timedelta(days=1)
        memory.entries[past_entry.id] = past_entry

        # Créer une entrée valide
        valid_entry = memory.remember(MemoryCategory.CONTEXT, "valid_key", "valid", "Valid entry")

        assert len(memory.entries) == 2

        # Cleanup
        cleaned = memory.cleanup_expired()

        assert cleaned == 1
        assert len(memory.entries) == 1
        assert "context:valid_key" in memory.entries
        assert "context:expired_key" not in memory.entries


class TestMemoryQuota:
    """Tests pour le quota max documents"""

    def test_quota_enforcement(self, monkeypatch):
        """Quand quota dépassé, doit purger 10% des plus anciennes"""
        monkeypatch.setattr(settings, "ENABLE_MEMORY_CLEANUP", True)
        monkeypatch.setattr(settings, "MEMORY_MAX_DOCUMENTS", 10)

        memory = DurableMemory(storage_path="/tmp/test_quota")

        # Remplir jusqu'au quota
        for i in range(10):
            memory.remember(MemoryCategory.CONTEXT, f"key_{i}", f"value_{i}", f"Entry {i}")

        assert len(memory.entries) == 10

        # Ajouter une 11ème entrée → doit déclencher purge de 10% (1 entrée)
        memory.remember(MemoryCategory.CONTEXT, "key_11", "value_11", "Entry 11")

        # Après purge: 10 - 1 (purge) + 1 (nouveau) = 10 entrées
        assert len(memory.entries) == 10

    def test_quota_disabled_when_cleanup_off(self, monkeypatch):
        """Avec ENABLE_MEMORY_CLEANUP=false, pas de quota enforcement"""
        monkeypatch.setattr(settings, "ENABLE_MEMORY_CLEANUP", False)
        monkeypatch.setattr(settings, "MEMORY_MAX_DOCUMENTS", 5)

        memory = DurableMemory(storage_path="/tmp/test_no_quota")

        # Dépasser le quota sans cleanup activé
        for i in range(10):
            memory.remember(MemoryCategory.CONTEXT, f"key_{i}", f"value_{i}", f"Entry {i}")

        # Pas de purge, toutes les entrées présentes
        assert len(memory.entries) == 10


class TestMemoryPersistence:
    """Tests pour la persistance des memories avec TTL"""

    def test_save_and_load_with_expiry(self, monkeypatch):
        """Les expiry_date doivent être sauvegardées et rechargées correctement"""
        monkeypatch.setattr(settings, "ENABLE_MEMORY_CLEANUP", True)
        monkeypatch.setattr(settings, "MEMORY_TTL_DAYS", 7)

        storage_path = "/tmp/test_persistence"
        memory1 = DurableMemory(storage_path=storage_path)

        # Créer une entrée avec TTL
        entry = memory1.remember(
            MemoryCategory.CONTEXT, "persist_key", "persist_value", "Persist test"
        )
        original_expiry = entry.expiry_date

        # Recharger depuis le fichier
        memory2 = DurableMemory(storage_path=storage_path)

        loaded_entry = memory2.entries.get("context:persist_key")
        assert loaded_entry is not None
        assert loaded_entry.expiry_date is not None
        assert loaded_entry.expiry_date == original_expiry


class TestSchedulerIntegration:
    """Tests pour l'intégration avec le scheduler"""

    def test_cleanup_task_callable(self):
        """La tâche cleanup_memory_task() doit être callable"""
        from app.core.scheduler import cleanup_memory_task

        # Vérifier que la fonction existe et est callable
        assert callable(cleanup_memory_task)

    def test_scheduler_config(self, monkeypatch):
        """Le scheduler doit utiliser MEMORY_CLEANUP_INTERVAL_HOURS"""
        monkeypatch.setattr(settings, "ENABLE_MEMORY_CLEANUP", True)
        monkeypatch.setattr(settings, "MEMORY_CLEANUP_INTERVAL_HOURS", 2)

        from app.core.scheduler import (APSCHEDULER_AVAILABLE, scheduler,
                                        start_scheduler)

        if not APSCHEDULER_AVAILABLE:
            pytest.skip("APScheduler not available")

        # Démarrer scheduler
        start_scheduler()

        # Vérifier que la job existe
        jobs = scheduler.get_jobs()
        memory_job = next((j for j in jobs if j.id == "memory_cleanup"), None)

        assert memory_job is not None
        assert memory_job.trigger.interval.total_seconds() == 2 * 3600  # 2 heures

        # Cleanup
        scheduler.shutdown(wait=False)
