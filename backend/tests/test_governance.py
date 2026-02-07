"""
Tests pour GovernanceManager - AI Orchestrator v7
"""

import asyncio
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.react_engine.governance import (ActionCategory,
                                                  ActionContext,
                                                  GovernanceManager,
                                                  RollbackInfo)


@pytest.fixture
def governance():
    """Fixture pour créer un manager de test"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield GovernanceManager(backup_dir=tmpdir)


class TestActionClassification:
    """Tests de classification des actions"""

    def test_read_actions(self, governance):
        """Les actions de lecture sont classifiées READ"""
        read_tools = ["read_file", "list_directory", "get_system_info", "git_status"]
        for tool in read_tools:
            category = governance.classify_action(tool, {})
            assert category == ActionCategory.READ, f"{tool} devrait être READ"

    def test_safe_actions(self, governance):
        """Les actions sûres sont classifiées SAFE"""
        category = governance.classify_action("calculate", {"expression": "1+1"})
        assert category == ActionCategory.SAFE

    def test_moderate_actions(self, governance):
        """Les actions modérées sont classifiées MODERATE"""
        category = governance.classify_action("run_tests", {})
        assert category == ActionCategory.MODERATE

    def test_sensitive_actions(self, governance):
        """Les actions sensibles sont classifiées SENSITIVE"""
        category = governance.classify_action("write_file", {"path": "/tmp/test"})
        assert category == ActionCategory.SENSITIVE

    def test_execute_command_by_role(self, governance):
        """execute_command est classifié selon le rôle"""
        # Viewer = SAFE
        cat_viewer = governance.classify_action(
            "execute_command", {"command": "ls", "role": "viewer"}
        )
        assert cat_viewer == ActionCategory.SAFE

        # Operator = MODERATE
        cat_operator = governance.classify_action(
            "execute_command", {"command": "docker ps", "role": "operator"}
        )
        assert cat_operator == ActionCategory.MODERATE

        # Admin = SENSITIVE
        cat_admin = governance.classify_action(
            "execute_command", {"command": "apt update", "role": "admin"}
        )
        assert cat_admin == ActionCategory.SENSITIVE


class TestVerificationRequirements:
    """Tests des exigences de vérification"""

    def test_read_no_verification(self, governance):
        """Les actions READ ne nécessitent pas de vérification"""
        assert governance.requires_verification(ActionCategory.READ) is False

    def test_safe_no_verification(self, governance):
        """Les actions SAFE ne nécessitent pas de vérification"""
        assert governance.requires_verification(ActionCategory.SAFE) is False

    def test_sensitive_requires_verification(self, governance):
        """Les actions SENSITIVE nécessitent vérification"""
        assert governance.requires_verification(ActionCategory.SENSITIVE) is True

    def test_critical_requires_verification(self, governance):
        """Les actions CRITICAL nécessitent vérification"""
        assert governance.requires_verification(ActionCategory.CRITICAL) is True


class TestActionPreparation:
    """Tests de préparation des actions"""

    @pytest.mark.asyncio
    async def test_prepare_read_action(self, governance):
        """Préparer une action READ réussit toujours"""
        approved, context, msg = await governance.prepare_action(
            "read_file", {"path": "/tmp/test.txt"}
        )
        assert approved is True
        assert context.category == ActionCategory.READ
        assert context.verification_required is False

    @pytest.mark.asyncio
    async def test_prepare_sensitive_without_justification(self, governance):
        """Action SENSITIVE sans justification est refusée"""
        approved, context, msg = await governance.prepare_action(
            "write_file", {"path": "/tmp/test.txt", "content": "test"}
        )
        assert approved is False
        assert "justification" in msg.lower()

    @pytest.mark.asyncio
    async def test_prepare_sensitive_with_justification(self, governance):
        """Action SENSITIVE avec justification est approuvée"""
        approved, context, msg = await governance.prepare_action(
            "write_file",
            {"path": "/tmp/test.txt", "content": "test"},
            justification="Mise à jour de configuration pour test",
        )
        assert approved is True
        assert context.verification_required is True

    @pytest.mark.asyncio
    async def test_action_history_recorded(self, governance):
        """Les actions sont enregistrées dans l'historique"""
        await governance.prepare_action("read_file", {"path": "/tmp/test"})
        await governance.prepare_action("list_directory", {"path": "/tmp"})

        history = governance.get_action_history()
        assert len(history) == 2


class TestRollback:
    """Tests du système de rollback"""

    @pytest.mark.asyncio
    async def test_rollback_for_sensitive_actions(self, governance):
        """Les actions SENSITIVE préparent un rollback"""
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("original content")
            temp_path = f.name

        try:
            approved, context, _ = await governance.prepare_action(
                "write_file",
                {"path": temp_path, "content": "new content"},
                justification="Test rollback",
            )

            assert approved is True
            assert context.rollback_data is not None
            assert context.action_id in governance.rollback_registry

        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_rollback_file_restore(self, governance):
        """Le rollback restaure le fichier original"""
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("original content")
            temp_path = f.name

        try:
            # Préparer l'action (crée le backup)
            approved, context, _ = await governance.prepare_action(
                "write_file",
                {"path": temp_path, "content": "new content"},
                justification="Test rollback",
            )

            # Simuler la modification du fichier
            with open(temp_path, "w") as f:
                f.write("new content")

            # Vérifier que le fichier a changé
            with open(temp_path, "r") as f:
                assert f.read() == "new content"

            # Effectuer le rollback
            success, msg = await governance.rollback(context.action_id)

            assert success is True

            # Vérifier que le fichier est restauré
            with open(temp_path, "r") as f:
                assert f.read() == "original content"

        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_rollback_nonexistent_action(self, governance):
        """Rollback d'une action inexistante échoue"""
        success, msg = await governance.rollback("nonexistent_action_id")
        assert success is False
        assert "pas de rollback" in msg.lower()


class TestRecordResult:
    """Tests d'enregistrement des résultats"""

    @pytest.mark.asyncio
    async def test_record_success(self, governance):
        """Enregistrer un succès met à jour le contexte"""
        approved, context, _ = await governance.prepare_action("read_file", {"path": "/tmp/test"})

        await governance.record_result(context.action_id, success=True, result={"content": "test"})

        # Vérifier que le contexte est mis à jour
        history = governance.get_action_history()
        action = [a for a in history if a["action_id"] == context.action_id][0]
        assert action["verified"] is True


class TestPendingVerifications:
    """Tests des vérifications en attente"""

    @pytest.mark.asyncio
    async def test_pending_verifications(self, governance):
        """Les actions SENSITIVE non vérifiées sont listées"""
        # Action READ (pas de vérification requise)
        await governance.prepare_action("read_file", {"path": "/tmp"})

        # Action SENSITIVE (vérification requise)
        await governance.prepare_action(
            "write_file", {"path": "/tmp/test", "content": "test"}, justification="Test"
        )

        pending = governance.get_pending_verifications()
        assert len(pending) == 1
        assert pending[0]["category"] == "sensitive"


class TestGovernanceBlocking:
    """Tests pour CRQ-P0-2: Gouvernance bloquante"""

    def test_governance_error_creation(self):
        """GovernanceError peut être créé avec métadonnées"""
        from app.services.react_engine.governance import GovernanceError

        error = GovernanceError("Test error", action_category="CRITICAL", action_id="test_123")

        assert str(error) == "Test error"
        assert error.action_category == "CRITICAL"
        assert error.action_id == "test_123"

    @pytest.mark.asyncio
    async def test_sensitive_action_without_justification_fails(self, governance):
        """Action SENSITIVE sans justification échoue (bloqué)"""
        approved, context, msg = await governance.prepare_action(
            "write_file", {"path": "/tmp/test.txt", "content": "test"}
        )

        # Doit être refusé sans justification
        assert approved is False
        assert "justification" in msg.lower()
        assert context.category == ActionCategory.SENSITIVE

    @pytest.mark.asyncio
    async def test_critical_action_always_requires_verification(self, governance):
        """Actions CRITICAL requièrent toujours vérification"""
        # Créer un contexte CRITICAL manuellement
        context = ActionContext(
            action_id="test_123",
            category=ActionCategory.CRITICAL,
            description="Test critical action",
            justification="Test justification",
        )

        # CRITICAL doit toujours requérir vérification
        assert governance.requires_verification(ActionCategory.CRITICAL) is True
        assert governance.requires_rollback(ActionCategory.CRITICAL) is True

    @pytest.mark.asyncio
    async def test_read_action_never_blocked(self, governance):
        """Actions READ ne sont jamais bloquées"""
        approved, context, msg = await governance.prepare_action(
            "read_file", {"path": "/tmp/test.txt"}
        )

        assert approved is True
        assert context.category == ActionCategory.READ
        assert context.verification_required is False


class TestGovernanceIntegration:
    """Tests d'intégration avec ToolRegistry (CRQ-P0-2)"""

    @pytest.mark.asyncio
    async def test_tool_execution_with_governance_blocking_disabled(self):
        """Test que l'exécution fonctionne avec ENFORCE_GOVERNANCE_BLOCKING=False"""
        from app.core.config import settings
        from app.services.react_engine.tools import ToolRegistry

        # S'assurer que le flag est désactivé
        original_value = settings.ENFORCE_GOVERNANCE_BLOCKING
        settings.ENFORCE_GOVERNANCE_BLOCKING = False

        try:
            registry = ToolRegistry()

            # Enregistrer un outil de test
            def test_tool():
                return {"success": True, "data": {"result": "ok"}, "error": None, "meta": {}}

            registry.register(
                name="test_read_tool",
                func=test_tool,
                description="Test tool",
                parameters={},
                category="utility",
            )

            # Exécuter l'outil devrait réussir même si gouvernance échoue
            result = await registry.execute("test_read_tool")
            assert result["success"] is True

        finally:
            settings.ENFORCE_GOVERNANCE_BLOCKING = original_value

    def test_governance_flag_default_value(self):
        """Vérifier que ENFORCE_GOVERNANCE_BLOCKING est False par défaut"""
        from app.core.config import Settings

        # Créer une nouvelle instance Settings sans .env
        test_settings = Settings(_env_file=None)

        # Le flag doit être False par défaut (backward compatibility)
        assert test_settings.ENFORCE_GOVERNANCE_BLOCKING is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
