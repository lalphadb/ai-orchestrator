"""
Tests des outils - AI Orchestrator v6.1
"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.react_engine.tools import BUILTIN_TOOLS, ok, fail


class TestToolsRegistry:
    """Tests du registre des outils"""
    
    def test_tools_count(self):
        """Doit avoir 16 outils"""
        tools = BUILTIN_TOOLS.list_tools()
        assert len(tools) == 16, f"Attendu 16 outils, obtenu {len(tools)}"
    
    def test_tools_have_required_fields(self):
        """Chaque outil doit avoir les champs requis"""
        required = ["name", "description", "category", "parameters"]
        for tool in BUILTIN_TOOLS.list_tools():
            for field in required:
                assert field in tool, f"Outil {tool.get('name')} manque {field}"
    
    def test_categories_exist(self):
        """Les catégories doivent être présentes"""
        categories = BUILTIN_TOOLS.get_categories()
        expected = {"system", "filesystem", "utility", "network", "qa"}
        assert set(categories) == expected
    
    def test_qa_tools_count(self):
        """Doit avoir 7 outils QA"""
        qa_tools = [t for t in BUILTIN_TOOLS.list_tools() if t["category"] == "qa"]
        assert len(qa_tools) == 7
    
    def test_qa_tools_names(self):
        """Les outils QA ont les bons noms"""
        qa_names = {t["name"] for t in BUILTIN_TOOLS.list_tools() if t["category"] == "qa"}
        expected = {"git_status", "git_diff", "run_tests", "run_lint", 
                   "run_format", "run_build", "run_typecheck"}
        assert qa_names == expected


class TestToolExecution:
    """Tests d'exécution des outils"""
    
    @pytest.mark.asyncio
    async def test_get_datetime(self):
        """get_datetime retourne la date/heure"""
        result = await BUILTIN_TOOLS.execute("get_datetime")
        assert result["success"] is True
        assert "datetime" in result["data"]
    
    @pytest.mark.asyncio
    async def test_calculate_basic(self):
        """calculate effectue des calculs basiques"""
        result = await BUILTIN_TOOLS.execute("calculate", expression="2 + 2")
        assert result["success"] is True
        assert result["data"]["result"] == 4
    
    @pytest.mark.asyncio
    async def test_calculate_invalid(self):
        """calculate refuse les expressions invalides"""
        result = await BUILTIN_TOOLS.execute("calculate", expression="import os")
        assert result["success"] is False


class TestToolResultFormat:
    """Tests du format de retour des outils"""
    
    @pytest.mark.asyncio
    async def test_success_format(self):
        """Les succès ont le bon format"""
        result = await BUILTIN_TOOLS.execute("get_datetime")
        assert "success" in result
        assert "data" in result
        assert "error" in result
        assert "meta" in result
        assert result["success"] is True
        assert result["error"] is None


class TestFilesystemTools:
    """Tests des outils filesystem"""
    
    @pytest.mark.asyncio
    async def test_read_file_in_workspace(self):
        """read_file fonctionne dans le workspace"""
        from app.core.config import settings
        test_file = Path(settings.WORKSPACE_DIR) / "test_read.txt"
        test_file.write_text("Hello Test")
        
        result = await BUILTIN_TOOLS.execute("read_file", path=str(test_file))
        assert result["success"] is True
        assert result["data"]["content"] == "Hello Test"
        
        test_file.unlink()
    
    @pytest.mark.asyncio
    async def test_write_file_in_workspace(self):
        """write_file fonctionne dans le workspace"""
        from app.core.config import settings
        test_file = Path(settings.WORKSPACE_DIR) / "test_write.txt"
        
        result = await BUILTIN_TOOLS.execute(
            "write_file", 
            path=str(test_file),
            content="Test content"
        )
        assert result["success"] is True
        assert test_file.exists()
        assert test_file.read_text() == "Test content"
        
        test_file.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
