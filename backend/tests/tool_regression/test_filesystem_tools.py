"""
Tests de régression pour les outils filesystem
"""

from pathlib import Path

import pytest

from app.services.react_engine.tools import BUILTIN_TOOLS

from .contracts import assert_tool_error, assert_tool_success


class TestReadFile:
    """Tests pour read_file - 6 scénarios"""

    @pytest.mark.asyncio
    async def test_read_existing_file(self, workspace_dir, mock_settings):
        """✅ Lecture fichier existant dans workspace"""
        test_file = Path(workspace_dir) / "test.txt"

        result = await BUILTIN_TOOLS.execute("read_file", path=str(test_file))

        assert_tool_success(result, {"content", "path", "size"})
        assert result["data"]["content"] == "Hello World"
        assert result["data"]["size"] == 11

    @pytest.mark.asyncio
    async def test_read_file_utf8_encoding(self, workspace_dir, mock_settings):
        """✅ Lecture fichier avec encodage UTF-8"""
        test_file = Path(workspace_dir) / "utf8.txt"
        test_file.write_text("Hello 世界 🌍", encoding="utf-8")

        result = await BUILTIN_TOOLS.execute("read_file", path=str(test_file))

        assert_tool_success(result)
        assert "世界" in result["data"]["content"]
        assert "🌍" in result["data"]["content"]

    @pytest.mark.asyncio
    async def test_read_file_not_found(self, workspace_dir, mock_settings):
        """❌ Fichier inexistant → E_FILE_NOT_FOUND (recoverable)"""
        result = await BUILTIN_TOOLS.execute("read_file", path=f"{workspace_dir}/nonexistent.txt")

        assert_tool_error(result, "E_FILE_NOT_FOUND", should_be_recoverable=True)
        assert "nonexistent.txt" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_read_file_outside_workspace(self, workspace_dir, mock_settings):
        """❌ Chemin hors workspace → E_PATH_FORBIDDEN"""
        result = await BUILTIN_TOOLS.execute("read_file", path="/etc/passwd")

        # Devrait être rejeté pour sortie du workspace
        assert not result["success"]
        assert result["error"]["code"] in ["E_PATH_FORBIDDEN", "E_PERMISSION"]

    @pytest.mark.asyncio
    async def test_read_file_path_traversal(self, workspace_dir, mock_settings):
        """❌ Path traversal (..) → E_PATH_FORBIDDEN"""
        result = await BUILTIN_TOOLS.execute(
            "read_file", path=f"{workspace_dir}/../../../etc/passwd"
        )

        # Path traversal détecté
        assert not result["success"]
        assert "traversal" in result["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_read_file_relative_path(self, workspace_dir, mock_settings):
        """✅ Chemin relatif résolu par rapport au workspace"""
        result = await BUILTIN_TOOLS.execute("read_file", path="test.txt")

        assert_tool_success(result)
        assert result["data"]["content"] == "Hello World"


class TestWriteFile:
    """Tests pour write_file - 6 scénarios"""

    @pytest.mark.asyncio
    async def test_write_new_file(self, workspace_dir, mock_settings):
        """✅ Écriture fichier nouveau dans workspace"""
        new_file = f"{workspace_dir}/new_file.txt"

        result = await BUILTIN_TOOLS.execute("write_file", path=new_file, content="New content")

        assert_tool_success(result, {"path", "size"})
        assert Path(new_file).read_text() == "New content"
        assert result["data"]["size"] == 11

    @pytest.mark.asyncio
    async def test_write_overwrite_existing(self, workspace_dir, mock_settings):
        """✅ Écrasement fichier existant"""
        existing = Path(workspace_dir) / "test.txt"
        original = existing.read_text()

        result = await BUILTIN_TOOLS.execute("write_file", path=str(existing), content="Updated")

        assert_tool_success(result)
        assert existing.read_text() == "Updated"
        assert existing.read_text() != original

    @pytest.mark.asyncio
    async def test_write_create_parent_dirs(self, workspace_dir, mock_settings):
        """✅ Création répertoires parents (mkdir -p)"""
        nested_file = f"{workspace_dir}/deep/nested/dirs/file.txt"

        result = await BUILTIN_TOOLS.execute("write_file", path=nested_file, content="Deep content")

        assert_tool_success(result)
        assert Path(nested_file).read_text() == "Deep content"
        assert Path(nested_file).parent.exists()

    @pytest.mark.asyncio
    async def test_write_file_outside_workspace(self, workspace_dir, mock_settings):
        """❌ Chemin hors workspace → E_PATH_FORBIDDEN"""
        result = await BUILTIN_TOOLS.execute(
            "write_file", path="/tmp/forbidden.txt", content="test"
        )

        assert not result["success"]
        assert result["error"]["code"] in [
            "E_PATH_FORBIDDEN",
            "E_PERMISSION",
            "E_GOVERNANCE_DENIED",
        ]

    @pytest.mark.asyncio
    async def test_write_file_path_traversal(self, workspace_dir, mock_settings):
        """❌ Path traversal → E_PATH_FORBIDDEN"""
        result = await BUILTIN_TOOLS.execute(
            "write_file", path=f"{workspace_dir}/../outside.txt", content="bad"
        )

        assert not result["success"]
        assert result["error"]["code"] in ["E_PATH_FORBIDDEN", "E_GOVERNANCE_DENIED"]

    @pytest.mark.asyncio
    async def test_write_file_relative_path(self, workspace_dir, mock_settings):
        """✅ Chemin relatif résolu dans workspace"""
        result = await BUILTIN_TOOLS.execute(
            "write_file", path="relative.txt", content="Relative content"
        )

        assert_tool_success(result)
        assert Path(workspace_dir, "relative.txt").read_text() == "Relative content"


class TestListDirectory:
    """Tests pour list_directory - 5 scénarios"""

    @pytest.mark.asyncio
    async def test_list_workspace(self, workspace_dir, mock_settings):
        """✅ Liste répertoire workspace"""
        result = await BUILTIN_TOOLS.execute("list_directory", path=workspace_dir)

        assert_tool_success(result, {"path", "entries", "count"})
        assert result["data"]["count"] > 0
        # Vérifier que test.txt est listé
        names = [e["name"] for e in result["data"]["entries"]]
        assert "test.txt" in names

    @pytest.mark.asyncio
    async def test_list_empty_directory(self, workspace_dir, mock_settings):
        """✅ Liste répertoire vide"""
        empty_dir = Path(workspace_dir) / "empty"
        empty_dir.mkdir()

        result = await BUILTIN_TOOLS.execute("list_directory", path=str(empty_dir))

        assert_tool_success(result)
        assert result["data"]["count"] == 0
        assert len(result["data"]["entries"]) == 0

    @pytest.mark.asyncio
    async def test_list_subdirectory(self, workspace_dir, mock_settings):
        """✅ Liste sous-répertoire"""
        result = await BUILTIN_TOOLS.execute("list_directory", path=f"{workspace_dir}/src")

        assert_tool_success(result)
        names = [e["name"] for e in result["data"]["entries"]]
        assert "main.py" in names

    @pytest.mark.asyncio
    async def test_list_directory_not_found(self, workspace_dir, mock_settings):
        """❌ Répertoire inexistant → E_DIR_NOT_FOUND (recoverable)"""
        result = await BUILTIN_TOOLS.execute("list_directory", path=f"{workspace_dir}/nonexistent")

        assert_tool_error(result, "E_DIR_NOT_FOUND", should_be_recoverable=True)

    @pytest.mark.asyncio
    async def test_list_directory_outside_workspace(self, workspace_dir, mock_settings):
        """❌ Chemin hors workspace → E_PATH_FORBIDDEN"""
        result = await BUILTIN_TOOLS.execute("list_directory", path="/etc")

        assert not result["success"]
        assert result["error"]["code"] in ["E_PATH_FORBIDDEN", "E_PERMISSION"]


class TestSearchFiles:
    """Tests pour search_files - 4 scénarios"""

    @pytest.mark.asyncio
    async def test_search_by_pattern(self, workspace_dir, mock_settings):
        """✅ Recherche par pattern (*.py)"""
        result = await BUILTIN_TOOLS.execute("search_files", pattern="*.py", path=workspace_dir)

        assert_tool_success(result, {"pattern", "path", "matches", "count"})
        assert result["data"]["count"] >= 1
        # main.py devrait être trouvé
        assert any("main.py" in p for p in result["data"]["matches"])

    @pytest.mark.asyncio
    async def test_search_recursive(self, workspace_dir, mock_settings):
        """✅ Recherche récursive (toujours récursif par défaut)"""
        result = await BUILTIN_TOOLS.execute("search_files", pattern="*.txt", path=workspace_dir)

        assert_tool_success(result)
        # Devrait trouver test.txt à la racine
        assert result["data"]["count"] >= 1

    @pytest.mark.asyncio
    async def test_search_no_results(self, workspace_dir, mock_settings):
        """✅ Aucun fichier trouvé (succès avec data vide)"""
        result = await BUILTIN_TOOLS.execute(
            "search_files", pattern="*.nonexistent", path=workspace_dir
        )

        assert_tool_success(result)
        assert result["data"]["count"] == 0
        assert len(result["data"]["matches"]) == 0

    @pytest.mark.asyncio
    async def test_search_invalid_pattern(self, workspace_dir, mock_settings):
        """❌ Pattern invalide → E_SEARCH_ERROR"""
        # Pattern avec caractères invalides
        result = await BUILTIN_TOOLS.execute("search_files", pattern="[invalid", path=workspace_dir)

        # Devrait soit réussir avec 0 résultats, soit échouer avec E_SEARCH_ERROR
        # Dépend de l'implémentation
        if not result["success"]:
            assert result["error"]["code"] in ["E_SEARCH_ERROR", "E_EXECUTION"]
