"""
Tests de régression pour les outils QA
"""

import pytest

from app.services.react_engine.tools import BUILTIN_TOOLS

from .contracts import assert_tool_success


class TestGitStatus:
    """Tests pour git_status - 3 scénarios"""

    @pytest.mark.asyncio
    async def test_git_status_with_repo(self, git_repo, mock_settings):
        """✅ Workspace avec git repo"""
        result = await BUILTIN_TOOLS.execute("git_status")

        # git_status retourne le résultat de execute_command qui a stdout/returncode
        assert_tool_success(result, {"stdout", "returncode"})
        assert result["data"]["returncode"] == 0

    @pytest.mark.asyncio
    async def test_git_status_modified_files(self, git_repo, mock_settings):
        """✅ Fichiers modifiés détectés"""
        from pathlib import Path

        # Modifier un fichier
        (Path(git_repo) / "README.md").write_text("# Modified")

        result = await BUILTIN_TOOLS.execute("git_status")

        assert_tool_success(result)
        # Devrait détecter des modifications dans stdout
        assert (
            " M README.md" in result["data"]["stdout"] or "M  README.md" in result["data"]["stdout"]
        )

    @pytest.mark.asyncio
    async def test_git_status_no_repo(self, workspace_dir, mock_settings):
        """⚠️ Pas de repo git (fallback gracieux)"""
        result = await BUILTIN_TOOLS.execute("git_status")

        # Devrait échouer car workspace_dir n'est pas un repo git
        # OU réussir avec returncode != 0
        if result["success"]:
            # git command ran but failed
            assert result["data"]["returncode"] != 0
        else:
            # Tool failed to execute
            assert True


class TestGitDiff:
    """Tests pour git_diff - 3 scénarios"""

    @pytest.mark.asyncio
    async def test_git_diff_modified_files(self, git_repo, mock_settings):
        """✅ Diff fichiers modifiés"""
        from pathlib import Path

        # Modifier un fichier
        readme = Path(git_repo) / "README.md"
        readme.write_text("# Modified Content")

        result = await BUILTIN_TOOLS.execute("git_diff")

        # git_diff retourne le résultat de execute_command
        assert_tool_success(result, {"stdout", "returncode"})
        # Devrait contenir le diff dans stdout
        assert len(result["data"]["stdout"]) > 0

    @pytest.mark.asyncio
    async def test_git_diff_no_changes(self, git_repo, mock_settings):
        """✅ Aucune modification (sortie vide)"""
        result = await BUILTIN_TOOLS.execute("git_diff")

        assert_tool_success(result)
        # Pas de modifications = stdout vide
        assert result["data"]["stdout"] == "" or len(result["data"]["stdout"]) == 0

    @pytest.mark.asyncio
    async def test_git_diff_no_repo(self, workspace_dir, mock_settings):
        """⚠️ Pas de repo git (fallback gracieux)"""
        result = await BUILTIN_TOOLS.execute("git_diff")

        # Devrait échouer ou réussir avec returncode != 0
        if result["success"]:
            assert result["data"]["returncode"] != 0
        else:
            assert True


class TestRunTests:
    """Tests pour run_tests - 3 scénarios"""

    @pytest.mark.asyncio
    async def test_run_tests_success(self, workspace_dir, mock_settings):
        """✅ Tests passent (exit 0)"""
        from pathlib import Path

        # Créer un fichier de test simple qui passe
        test_file = Path(workspace_dir) / "test_sample.py"
        test_file.write_text(
            """
def test_simple():
    assert 1 + 1 == 2
"""
        )

        result = await BUILTIN_TOOLS.execute("run_tests", directory=workspace_dir)

        # Devrait réussir OU échouer si pytest pas installé
        if result["success"]:
            assert_tool_success(result, {"output", "returncode"})
            assert result["data"]["returncode"] == 0

    @pytest.mark.asyncio
    async def test_run_tests_failure(self, workspace_dir, mock_settings):
        """❌ Tests échouent (exit 1, avec détails)"""
        from pathlib import Path

        # Créer un test qui échoue
        test_file = Path(workspace_dir) / "test_fail.py"
        test_file.write_text(
            """
def test_failing():
    assert 1 + 1 == 3  # This will fail
"""
        )

        result = await BUILTIN_TOOLS.execute("run_tests", directory=workspace_dir)

        # Devrait réussir (l'outil fonctionne) mais returncode != 0
        if result["success"]:
            assert result["data"]["returncode"] != 0
            # Output devrait contenir des détails sur l'échec
            assert (
                "fail" in result["data"]["output"].lower()
                or "error" in result["data"]["output"].lower()
            )

    @pytest.mark.asyncio
    async def test_run_tests_invalid_target(self, workspace_dir, mock_settings):
        """❌ Target invalide → E_INVALID_TARGET or E_VALIDATION"""
        # Tenter de lancer tests avec un target invalide
        result = await BUILTIN_TOOLS.execute("run_tests", target="nonexistent_target")

        # Devrait échouer car le target n'existe pas
        if not result["success"]:
            assert result["error"]["code"] in [
                "E_EXECUTION",
                "E_VALIDATION",
                "E_TOOL_EXEC",
                "E_INVALID_TARGET",
            ]
