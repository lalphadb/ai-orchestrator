"""
Fixtures communes pour les tests de régression des outils
"""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Ajouter le backend au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def workspace_dir(tmp_path):
    """
    Créer un workspace temporaire pour les tests.
    Utilise tmp_path de pytest pour isolation complète.
    """
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    # Créer quelques fichiers/répertoires de test
    (workspace / "test.txt").write_text("Hello World")
    (workspace / "data").mkdir()
    (workspace / "data" / "file.json").write_text('{"key": "value"}')
    (workspace / "src").mkdir()
    (workspace / "src" / "main.py").write_text("print('hello')")

    return str(workspace)


@pytest.fixture
def test_file(workspace_dir):
    """Créer un fichier de test dans le workspace"""
    test_path = Path(workspace_dir) / "test_file.txt"
    test_path.write_text("test content")
    return str(test_path)


@pytest.fixture
def mock_ollama(monkeypatch):
    """
    Mock des réponses Ollama pour list_llm_models.
    Évite les appels réseau réels pendant les tests.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [
            {
                "name": "mistral:latest",
                "size": 4000000000,
                "modified_at": "2024-01-01T00:00:00Z",
            },
            {
                "name": "deepseek-coder:33b",
                "size": 18000000000,
                "modified_at": "2024-01-01T00:00:00Z",
            },
            {
                "name": "kimi-k2:1t-cloud",
                "size": 100,  # Cloud model (small size)
                "modified_at": "2024-01-01T00:00:00Z",
            },
        ]
    }

    async def mock_get(*args, **kwargs):
        return mock_response

    # Patch httpx.AsyncClient
    import httpx

    mock_client = AsyncMock()
    mock_client.get = mock_get
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    original_client = httpx.AsyncClient

    def mock_async_client(*args, **kwargs):
        return mock_client

    monkeypatch.setattr(httpx, "AsyncClient", mock_async_client)

    return mock_response


@pytest.fixture
def mock_ollama_unavailable(monkeypatch):
    """Mock Ollama non disponible (pour tester les erreurs)"""
    mock_response = MagicMock()
    mock_response.status_code = 500

    async def mock_get(*args, **kwargs):
        return mock_response

    import httpx

    mock_client = AsyncMock()
    mock_client.get = mock_get
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    def mock_async_client(*args, **kwargs):
        return mock_client

    monkeypatch.setattr(httpx, "AsyncClient", mock_async_client)

    return mock_response


@pytest.fixture
def mock_http_success(monkeypatch):
    """Mock requête HTTP réussie"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"message": "success"}'
    mock_response.headers = {"content-type": "application/json"}

    async def mock_get(*args, **kwargs):
        return mock_response

    async def mock_post(*args, **kwargs):
        return mock_response

    import httpx

    mock_client = AsyncMock()
    mock_client.get = mock_get
    mock_client.post = mock_post
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    def mock_async_client(*args, **kwargs):
        return mock_client

    monkeypatch.setattr(httpx, "AsyncClient", mock_async_client)

    return mock_response


@pytest.fixture
def mock_http_timeout(monkeypatch):
    """Mock timeout HTTP"""

    async def mock_request(*args, **kwargs):
        import httpx

        raise httpx.TimeoutException("Request timeout")

    import httpx

    mock_client = AsyncMock()
    mock_client.request = mock_request
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    def mock_async_client(*args, **kwargs):
        return mock_client

    monkeypatch.setattr(httpx, "AsyncClient", mock_async_client)


@pytest.fixture
def git_repo(workspace_dir):
    """
    Initialiser un repo git dans le workspace pour les tests git.
    Skip si git n'est pas disponible.
    """
    import subprocess

    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True, timeout=2)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pytest.skip("git not available")

    # Initialiser repo
    subprocess.run(["git", "init"], cwd=workspace_dir, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=workspace_dir,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=workspace_dir,
        capture_output=True,
        check=True,
    )

    # Commit initial
    (Path(workspace_dir) / "README.md").write_text("# Test Repo")
    subprocess.run(["git", "add", "."], cwd=workspace_dir, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=workspace_dir,
        capture_output=True,
        check=True,
    )

    return workspace_dir


@pytest.fixture(autouse=True)
def set_testing_env(monkeypatch):
    """
    Définir TESTING=1 pour tous les tests de régression.
    Désactive rate limiting et autres fonctionnalités dépendantes de l'environnement.
    """
    monkeypatch.setenv("TESTING", "1")


@pytest.fixture(autouse=True)
def bypass_governance(monkeypatch):
    """
    Auto-approve governance for all tool regression tests.
    Governance is tested separately in test_security.py.
    """
    from app.services.react_engine.governance import (ActionCategory,
                                                      ActionContext,
                                                      governance_manager)

    async def auto_approve(tool_name, params, justification=""):
        action_id = governance_manager._generate_action_id()
        category = governance_manager.classify_action(tool_name, params)
        context = ActionContext(
            action_id=action_id,
            category=category,
            description=f"{tool_name}({params})",
            justification="test-auto-approved",
            verification_required=False,
        )
        return True, context, "Auto-approved for testing"

    monkeypatch.setattr(governance_manager, "prepare_action", auto_approve)


@pytest.fixture
def mock_settings(workspace_dir, monkeypatch):
    """
    Override settings.WORKSPACE_DIR pour utiliser le workspace temporaire.
    """
    from app.core.config import settings

    monkeypatch.setattr(settings, "WORKSPACE_DIR", workspace_dir)
    return settings
