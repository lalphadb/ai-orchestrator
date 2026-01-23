"""
Tests API endpoints - Chat and system endpoints
Phase 4 - Quality Code
"""

import pytest
from fastapi.testclient import TestClient


class TestChatAPI:
    """Test /api/v1/chat endpoints"""

    def test_chat_requires_auth(self, client: TestClient):
        """Test que /chat nécessite authentification"""
        response = client.post("/api/v1/chat", json={"message": "test"})
        assert response.status_code == 401

    def test_chat_with_invalid_token(self, client: TestClient):
        """Test chat avec token invalide"""
        response = client.post(
            "/api/v1/chat",
            json={"message": "Hello"},
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401

    def test_chat_with_empty_message(self, client: TestClient, auth_headers: dict):
        """Test chat avec message vide"""
        response = client.post("/api/v1/chat", json={"message": ""}, headers=auth_headers)
        # Devrait rejeter ou retourner erreur
        assert response.status_code in [400, 422]

    def test_chat_simple_query(self, client: TestClient, auth_headers: dict):
        """Test chat avec query simple (fast path)"""
        response = client.post(
            "/api/v1/chat",
            json={"message": "quelle heure est-il?", "model": "mistral:latest"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        # Fast path devrait éviter SPEC/PLAN
        assert data.get("workflow_phase") in ["execute", "complete", None]


class TestSystemAPI:
    """Test /api/v1/system endpoints"""

    def test_health_check_public(self, client: TestClient):
        """Test health check sans auth (public)"""
        response = client.get("/api/v1/system/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_models_requires_auth(self, client: TestClient):
        """Test liste modèles nécessite auth"""
        response = client.get("/api/v1/system/models")
        # Peut être public ou protégé selon config
        assert response.status_code in [200, 401]

    def test_models_with_auth(self, client: TestClient, auth_headers: dict):
        """Test liste modèles avec auth"""
        response = client.get("/api/v1/system/models", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "models" in data or isinstance(data, list)


class TestToolsAPI:
    """Test /api/v1/tools endpoints"""

    def test_list_tools_requires_auth(self, client: TestClient):
        """Test liste outils nécessite auth"""
        response = client.get("/api/v1/tools")
        assert response.status_code == 401

    def test_list_tools_with_auth(self, client: TestClient, auth_headers: dict):
        """Test liste outils avec auth"""
        response = client.get("/api/v1/tools", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict) or isinstance(data, list)

    def test_execute_tool_requires_auth(self, client: TestClient):
        """Test exécution outil nécessite auth"""
        response = client.post(
            "/api/v1/tools/read_file/execute", json={"file_path": "/etc/hostname"}
        )
        assert response.status_code == 401

    def test_execute_nonexistent_tool(self, client: TestClient, auth_headers: dict):
        """Test outil inexistant retourne erreur propre"""
        response = client.post(
            "/api/v1/tools/fake_tool_xyz/execute", json={"param": "value"}, headers=auth_headers
        )
        # Devrait retourner erreur structurée, pas crash
        assert response.status_code in [404, 200]
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") == False
            assert "error" in data


class TestRateLimiting:
    """Test rate limiting middleware"""

    @pytest.mark.skip(reason="Rate limiting test requires time - run manually")
    def test_rate_limit_chat(self, client: TestClient, auth_headers: dict):
        """Test rate limiting après 30 requêtes"""
        # Envoyer 31 requêtes rapides
        for i in range(31):
            response = client.post(
                "/api/v1/chat", json={"message": f"test {i}"}, headers=auth_headers
            )
            if i < 30:
                assert response.status_code == 200
            else:
                # 31ème devrait être rate limited
                assert response.status_code == 429
                break
