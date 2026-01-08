"""Configuration pytest pour AI Orchestrator v6.1"""
import pytest
import sys
from pathlib import Path

# Ajouter le backend au path
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture
def workspace_dir():
    """Retourne le chemin du workspace"""
    from app.core.config import settings
    return settings.WORKSPACE_DIR

@pytest.fixture
def test_file(workspace_dir, tmp_path):
    """Crée un fichier de test temporaire dans le workspace"""
    from pathlib import Path
    test_path = Path(workspace_dir) / "pytest_temp.txt"
    test_path.write_text("test content")
    yield test_path
    if test_path.exists():
        test_path.unlink()
