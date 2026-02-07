"""
Tests de régression pour les outils network
"""

import pytest

from app.services.react_engine.tools import BUILTIN_TOOLS

from .contracts import assert_tool_error, assert_tool_success


class TestHTTPRequest:
    """Tests pour http_request - 5 scénarios"""

    @pytest.mark.asyncio
    async def test_http_get_success(self, mock_http_success):
        """✅ GET request succès (200)"""
        result = await BUILTIN_TOOLS.execute(
            "http_request", url="https://api.example.com/data", method="GET"
        )

        assert_tool_success(result, {"status_code", "body", "headers"})
        assert result["data"]["status_code"] == 200
        assert "success" in result["data"]["body"]

    @pytest.mark.asyncio
    async def test_http_post_with_json(self, mock_http_success):
        """✅ POST avec body JSON"""
        result = await BUILTIN_TOOLS.execute(
            "http_request",
            url="https://api.example.com/submit",
            method="POST",
            data={"key": "value"},
        )

        assert_tool_success(result)
        assert result["data"]["status_code"] == 200

    @pytest.mark.asyncio
    async def test_http_ssrf_blocked_localhost(self):
        """❌ URL SSRF bloquée (localhost) → E_URL_FORBIDDEN"""
        result = await BUILTIN_TOOLS.execute(
            "http_request", url="http://localhost:8080/admin", method="GET"
        )

        # SSRF protection devrait bloquer localhost
        assert_tool_error(result, "E_URL_FORBIDDEN", should_be_recoverable=False)
        assert (
            "interdit" in result["error"]["message"].lower()
            or "localhost" in result["error"]["message"].lower()
        )

    @pytest.mark.asyncio
    async def test_http_ssrf_blocked_private_ip(self):
        """❌ URL SSRF bloquée (169.254.x.x) → E_URL_FORBIDDEN"""
        result = await BUILTIN_TOOLS.execute(
            "http_request", url="http://169.254.169.254/latest/meta-data", method="GET"
        )

        # SSRF protection devrait bloquer IP privées
        assert_tool_error(result, "E_URL_FORBIDDEN", should_be_recoverable=False)
        assert (
            "interdit" in result["error"]["message"].lower()
            or "privé" in result["error"]["message"].lower()
            or "metadata" in result["error"]["message"].lower()
        )

    @pytest.mark.asyncio
    async def test_http_timeout(self, mock_http_timeout):
        """❌ Timeout → E_HTTP_ERROR or E_HTTP_TIMEOUT"""
        result = await BUILTIN_TOOLS.execute(
            "http_request", url="https://slow-api.example.com/data", method="GET"
        )

        # Devrait timeout
        assert not result["success"]
        assert result["error"]["code"] in ["E_HTTP_TIMEOUT", "E_HTTP_ERROR"]
        assert result["error"]["recoverable"] is False

    @pytest.mark.asyncio
    async def test_http_404_not_error(self, mock_http_success):
        """✅ HTTP 404 → Succès avec status_code dans data"""
        # Modifier le mock pour retourner 404
        mock_http_success.status_code = 404
        mock_http_success.text = "Not Found"

        result = await BUILTIN_TOOLS.execute(
            "http_request", url="https://api.example.com/notfound", method="GET"
        )

        # HTTP errors (404, 500) ne sont PAS des tool errors
        # L'outil réussit, mais status_code indique l'erreur HTTP
        assert_tool_success(result)
        assert result["data"]["status_code"] == 404
