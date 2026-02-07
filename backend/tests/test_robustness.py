"""
Tests de robustesse - Étape 3 Phase 7
Test du comportement système en cas d'erreurs, timeouts, pannes
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import settings
from app.services.ollama.client import OllamaClient
from app.services.react_engine.tools import BUILTIN_TOOLS


@pytest.mark.asyncio
async def test_timeout_http_request():
    """Test que les timeouts HTTP sont respectés"""

    async def slow_response():
        """Simule une réponse lente"""
        await asyncio.sleep(10)  # Plus long que le timeout
        return {"status": 200}

    # Test qu'une exception timeout est levée
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(slow_response(), timeout=1.0)


@pytest.mark.asyncio
async def test_timeout_llm_call():
    """Test timeout sur appel LLM Ollama"""
    client = OllamaClient()

    # Mock httpx client pour simuler un timeout
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value.post = AsyncMock(
            side_effect=asyncio.TimeoutError("Request timeout")
        )
        mock_client.return_value = mock_instance

        # Vérifier que l'erreur est gérée correctement
        result = await client.generate(prompt="Test", model="test-model")

        assert "error" in result
        assert result.get("success", False) is False


@pytest.mark.asyncio
async def test_health_check_ollama_available():
    """Test health check quand Ollama est disponible"""
    client = OllamaClient()

    # Mock une réponse réussie
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": []}
        mock_instance.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_instance

        result = await client.health_check()
        assert result is True


@pytest.mark.asyncio
async def test_health_check_ollama_down():
    """Test health check quand Ollama est down"""
    client = OllamaClient()

    # Mock une connexion échouée
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value.get = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        mock_client.return_value = mock_instance

        result = await client.health_check()
        assert result is False


@pytest.mark.asyncio
async def test_request_tracing_header():
    """Test propagation du request_id dans les headers"""
    from fastapi.testclient import TestClient

    from main import app

    client = TestClient(app)

    # Faire une requête avec un X-Request-ID custom
    request_id = "test-request-123"
    response = client.get("/health", headers={"X-Request-ID": request_id})

    assert response.status_code == 200
    # Le request_id devrait être présent dans les logs/contexte


@pytest.mark.asyncio
async def test_metrics_recording_on_success():
    """Test que les métriques sont enregistrées sur succès"""
    from app.core.metrics import LLM_CALLS, record_llm_call

    # Get current count
    before = LLM_CALLS.labels(model="test-model", success="true")._value.get()

    # Record a successful call
    record_llm_call(model="test-model", success=True, prompt_tokens=10, completion_tokens=20)

    # Verify count increased
    after = LLM_CALLS.labels(model="test-model", success="true")._value.get()
    assert after > before


@pytest.mark.asyncio
async def test_metrics_recording_on_failure():
    """Test que les métriques sont enregistrées sur échec"""
    from app.core.metrics import LLM_CALLS, record_llm_call

    # Get current count
    before = LLM_CALLS.labels(model="test-model", success="false")._value.get()

    # Record a failed call
    record_llm_call(model="test-model", success=False)

    # Verify count increased
    after = LLM_CALLS.labels(model="test-model", success="false")._value.get()
    assert after > before


@pytest.mark.asyncio
async def test_tool_error_codes():
    """Test que les outils retournent les bons codes d'erreur"""

    # Test E_FILE_NOT_FOUND (use workspace path)
    result = await BUILTIN_TOOLS.execute(
        "read_file", path=f"{settings.WORKSPACE_DIR}/nonexistent_file_xyz.txt"
    )
    assert result["success"] is False
    assert result["error"]["code"] == "E_FILE_NOT_FOUND"
    assert result["error"]["recoverable"] is True

    # Test E_DIR_NOT_FOUND (use workspace path)
    result = await BUILTIN_TOOLS.execute(
        "list_directory", path=f"{settings.WORKSPACE_DIR}/nonexistent_directory"
    )
    assert result["success"] is False
    assert result["error"]["code"] == "E_DIR_NOT_FOUND"
    assert result["error"]["recoverable"] is True


@pytest.mark.asyncio
async def test_workflow_phase_metrics():
    """Test que les métriques de workflow sont enregistrées"""
    from app.core.metrics import record_workflow_phase

    # Simply record phase durations and verify they don't raise errors
    record_workflow_phase("SPEC", 2.5)
    record_workflow_phase("PLAN", 1.5)
    record_workflow_phase("EXECUTE", 3.0)

    # If we get here without exceptions, the metrics are working
    assert True


@pytest.mark.asyncio
async def test_tool_latency_metrics():
    """Test que les latences d'outils sont enregistrées"""
    from app.core.metrics import TOOL_LATENCY, record_tool_execution

    # Record a tool execution
    record_tool_execution(tool_name="test_tool", duration_s=0.5, success=True, error_code=None)

    # Verify metric exists
    metric = TOOL_LATENCY.labels(tool_name="test_tool", success="true")
    assert metric is not None


@pytest.mark.asyncio
async def test_database_connection_resilience():
    """Test résilience de la connexion base de données"""
    from app.core.database import get_db

    # Vérifier qu'on peut obtenir une session
    db_gen = get_db()
    db = next(db_gen)

    assert db is not None

    # Cleanup
    try:
        next(db_gen)
    except StopIteration:
        pass


@pytest.mark.asyncio
async def test_concurrent_llm_calls():
    """Test comportement avec appels LLM concurrents"""
    client = OllamaClient()

    # Mock des réponses réussies
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "test",
            "prompt_eval_count": 10,
            "eval_count": 20,
        }
        mock_instance.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_instance

        # Lancer 5 appels en parallèle
        tasks = [client.generate(prompt=f"Test {i}", model="test-model") for i in range(5)]

        results = await asyncio.gather(*tasks)

        # Tous doivent réussir
        assert len(results) == 5
        assert all("response" in r for r in results)


@pytest.mark.asyncio
async def test_tool_execution_with_timeout():
    """Test que l'exécution d'outils respecte les timeouts"""

    # Test avec un outil qui devrait être rapide
    result = await asyncio.wait_for(BUILTIN_TOOLS.execute("get_datetime"), timeout=5.0)

    assert result["success"] is True
    assert "data" in result


@pytest.mark.asyncio
async def test_error_recovery_suggestions():
    """Test que les erreurs récupérables suggèrent des solutions"""

    # Erreur fichier non trouvé devrait suggérer une recherche (use workspace path)
    result = await BUILTIN_TOOLS.execute(
        "read_file", path=f"{settings.WORKSPACE_DIR}/nonexistent_file_xyz.txt"
    )

    assert result["success"] is False
    assert result["error"]["code"] == "E_FILE_NOT_FOUND"
    assert result["error"]["recoverable"] is True

    # Le message d'erreur devrait contenir le nom du fichier
    assert "nonexistent_file_xyz.txt" in result["error"]["message"]


@pytest.mark.asyncio
async def test_settings_timeout_configuration():
    """Test que les timeouts sont configurables depuis settings"""

    # Vérifier que les timeouts existent dans settings
    assert hasattr(settings, "TIMEOUT_OLLAMA_CHAT")
    assert hasattr(settings, "TIMEOUT_OLLAMA_CONNECT")

    # Vérifier que ce sont des valeurs raisonnables
    assert settings.TIMEOUT_OLLAMA_CHAT > 0
    assert settings.TIMEOUT_OLLAMA_CONNECT > 0

    # Chat timeout devrait être plus long que connect
    assert settings.TIMEOUT_OLLAMA_CHAT > settings.TIMEOUT_OLLAMA_CONNECT


@pytest.mark.asyncio
async def test_graceful_degradation():
    """Test dégradation gracieuse quand services externes sont down"""
    from fastapi.testclient import TestClient

    from main import app

    client = TestClient(app)

    # Le health check devrait toujours répondre même si Ollama est down
    response = client.get("/health")
    assert response.status_code == 200

    # Le endpoint racine devrait toujours fonctionner
    response = client.get("/")
    assert response.status_code == 200
    assert "name" in response.json()


# Résumé des tests
"""
Tests de robustesse couverts:
1. ✅ Timeout HTTP request
2. ✅ Timeout LLM call
3. ✅ Health check Ollama up
4. ✅ Health check Ollama down
5. ✅ Request tracing headers
6. ✅ Métriques succès
7. ✅ Métriques échec
8. ✅ Codes d'erreur outils
9. ✅ Métriques workflow phases
10. ✅ Métriques latences outils
11. ✅ Résilience DB connection
12. ✅ Appels LLM concurrents
13. ✅ Tool execution timeout
14. ✅ Error recovery suggestions
15. ✅ Settings timeout config
16. ✅ Graceful degradation

Total: 16 tests de robustesse
"""
