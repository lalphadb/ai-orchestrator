"""
Tests pour SecureExecutor - AI Orchestrator v7
Vérifie la sécurité et le bon fonctionnement
"""

import pytest
import asyncio
import sys
import os

# Ajouter le chemin du backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.react_engine.secure_executor import (
    SecureExecutor, 
    ExecutionRole, 
    ExecutionResult,
    FORBIDDEN_CHARS
)


@pytest.fixture
def executor():
    """Fixture pour créer un executor de test"""
    return SecureExecutor(workspace_dir="/tmp/test-workspace")


class TestSecurityBlocking:
    """Tests de blocage des commandes dangereuses"""
    
    @pytest.mark.asyncio
    async def test_block_shell_injection_semicolon(self, executor):
        """Bloque ; pour chaînage de commandes"""
        result = await executor.execute("ls; rm -rf /", role=ExecutionRole.ADMIN)
        assert not result.success
        assert result.error_code == "E_PARSE_ERROR"
        assert "interdit" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_block_shell_injection_and(self, executor):
        """Bloque && pour chaînage"""
        result = await executor.execute("ls && cat /etc/passwd", role=ExecutionRole.ADMIN)
        assert not result.success
        assert result.error_code == "E_PARSE_ERROR"
    
    @pytest.mark.asyncio
    async def test_block_shell_injection_or(self, executor):
        """Bloque || pour chaînage"""
        result = await executor.execute("false || rm -rf /", role=ExecutionRole.ADMIN)
        assert not result.success
        assert result.error_code == "E_PARSE_ERROR"
    
    @pytest.mark.asyncio
    async def test_block_pipe(self, executor):
        """Bloque | pour pipe"""
        result = await executor.execute("cat /etc/passwd | grep root", role=ExecutionRole.ADMIN)
        assert not result.success
        assert result.error_code == "E_PARSE_ERROR"
    
    @pytest.mark.asyncio
    async def test_block_command_substitution_backtick(self, executor):
        """Bloque `cmd` substitution"""
        result = await executor.execute("echo `whoami`", role=ExecutionRole.ADMIN)
        assert not result.success
        assert result.error_code == "E_PARSE_ERROR"
    
    @pytest.mark.asyncio
    async def test_block_command_substitution_dollar(self, executor):
        """Bloque $(cmd) substitution"""
        result = await executor.execute("echo $(whoami)", role=ExecutionRole.ADMIN)
        assert not result.success
        assert result.error_code == "E_PARSE_ERROR"
    
    @pytest.mark.asyncio
    async def test_block_redirect_output(self, executor):
        """Bloque > redirection"""
        result = await executor.execute("echo test > /tmp/file", role=ExecutionRole.ADMIN)
        assert not result.success
        assert result.error_code == "E_PARSE_ERROR"
    
    @pytest.mark.asyncio
    async def test_block_redirect_input(self, executor):
        """Bloque < redirection"""
        result = await executor.execute("cat < /etc/passwd", role=ExecutionRole.ADMIN)
        assert not result.success
        assert result.error_code == "E_PARSE_ERROR"


class TestRolePermissions:
    """Tests des permissions par rôle"""
    
    @pytest.mark.asyncio
    async def test_viewer_can_ls(self, executor):
        """Viewer peut faire ls"""
        result = await executor.execute("ls /tmp", role=ExecutionRole.VIEWER)
        assert result.success or result.error_code == "E_CMD_FAILED"  # Peut échouer si /tmp vide
        assert result.error_code != "E_NOT_ALLOWED"
    
    @pytest.mark.asyncio
    async def test_viewer_cannot_apt(self, executor):
        """Viewer ne peut pas faire apt"""
        result = await executor.execute("apt update", role=ExecutionRole.VIEWER)
        assert not result.success
        assert result.error_code == "E_NOT_ALLOWED"
    
    @pytest.mark.asyncio
    async def test_viewer_cannot_mkdir(self, executor):
        """Viewer ne peut pas faire mkdir"""
        result = await executor.execute("mkdir /tmp/test", role=ExecutionRole.VIEWER)
        assert not result.success
        assert result.error_code == "E_NOT_ALLOWED"
    
    @pytest.mark.asyncio
    async def test_operator_can_systemctl(self, executor):
        """Operator peut faire systemctl"""
        result = await executor.execute("systemctl status", role=ExecutionRole.OPERATOR)
        # Peut réussir ou échouer selon le système, mais doit être autorisé
        assert result.error_code != "E_NOT_ALLOWED"
    
    @pytest.mark.asyncio
    async def test_admin_can_mkdir(self, executor):
        """Admin peut faire mkdir"""
        result = await executor.execute("mkdir -p /tmp/test-secure-exec", role=ExecutionRole.ADMIN)
        assert result.error_code != "E_NOT_ALLOWED"
    
    @pytest.mark.asyncio
    async def test_unknown_command_blocked(self, executor):
        """Commande inconnue bloquée"""
        result = await executor.execute("malicious_command", role=ExecutionRole.ADMIN)
        assert not result.success
        assert result.error_code == "E_NOT_ALLOWED"


class TestValidCommands:
    """Tests des commandes valides"""
    
    @pytest.mark.asyncio
    async def test_simple_ls(self, executor):
        """ls simple fonctionne"""
        result = await executor.execute("ls /", role=ExecutionRole.VIEWER)
        assert result.success
        assert "bin" in result.stdout or "etc" in result.stdout
    
    @pytest.mark.asyncio
    async def test_pwd(self, executor):
        """pwd fonctionne"""
        result = await executor.execute("pwd", role=ExecutionRole.VIEWER)
        assert result.success
        assert "/" in result.stdout
    
    @pytest.mark.asyncio
    async def test_date(self, executor):
        """date fonctionne"""
        result = await executor.execute("date", role=ExecutionRole.VIEWER)
        assert result.success
        assert "202" in result.stdout  # Année 202x
    
    @pytest.mark.asyncio
    async def test_hostname(self, executor):
        """hostname fonctionne"""
        result = await executor.execute("hostname", role=ExecutionRole.VIEWER)
        assert result.success
        assert len(result.stdout.strip()) > 0
    
    @pytest.mark.asyncio
    async def test_df(self, executor):
        """df fonctionne"""
        result = await executor.execute("df -h", role=ExecutionRole.VIEWER)
        assert result.success
        assert "Filesystem" in result.stdout or "Sys." in result.stdout


class TestAuditLog:
    """Tests du système d'audit"""
    
    @pytest.mark.asyncio
    async def test_audit_successful_command(self, executor):
        """Audit enregistre les commandes réussies"""
        await executor.execute("pwd", role=ExecutionRole.VIEWER)
        
        log = executor.get_audit_log(last_n=1)
        assert len(log) >= 1
        assert log[-1]["allowed"] == True
        assert log[-1]["role"] == "viewer"
        assert "pwd" in log[-1]["command"]
    
    @pytest.mark.asyncio
    async def test_audit_blocked_command(self, executor):
        """Audit enregistre les commandes bloquées"""
        await executor.execute("rm -rf /", role=ExecutionRole.ADMIN)
        
        log = executor.get_audit_log(last_n=1)
        assert len(log) >= 1
        assert log[-1]["allowed"] == False
    
    @pytest.mark.asyncio
    async def test_audit_denied_command(self, executor):
        """Audit enregistre les commandes refusées (permission)"""
        await executor.execute("apt update", role=ExecutionRole.VIEWER)
        
        log = executor.get_audit_log(last_n=1)
        assert len(log) >= 1
        assert log[-1]["allowed"] == False
        assert "non autorisée" in log[-1]["reason"]


class TestEdgeCases:
    """Tests des cas limites"""
    
    @pytest.mark.asyncio
    async def test_empty_command(self, executor):
        """Commande vide rejetée"""
        result = await executor.execute("", role=ExecutionRole.ADMIN)
        assert not result.success
    
    @pytest.mark.asyncio
    async def test_whitespace_command(self, executor):
        """Commande whitespace rejetée"""
        result = await executor.execute("   ", role=ExecutionRole.ADMIN)
        assert not result.success
    
    @pytest.mark.asyncio
    async def test_command_with_quotes(self, executor):
        """Commande avec quotes gérée correctement"""
        result = await executor.execute('ls "/tmp"', role=ExecutionRole.VIEWER)
        assert result.error_code != "E_PARSE_ERROR"
    
    @pytest.mark.asyncio
    async def test_timeout(self, executor):
        """Timeout fonctionne"""
        # sleep n'est pas dans la liste autorisée, donc tester avec une autre approche
        result = await executor.execute("find / -name 'impossible*'", role=ExecutionRole.VIEWER, timeout=1)
        # Soit timeout, soit la commande termine
        assert result.error_code in ["E_TIMEOUT", None, "E_CMD_FAILED"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
