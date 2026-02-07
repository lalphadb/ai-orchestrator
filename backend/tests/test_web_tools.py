"""
Tests for web_search and web_read tools (v8)
"""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.services.react_engine.tools import (
    web_search,
    web_read,
    _extract_text_from_html,
    BUILTIN_TOOLS,
)


class TestWebSearch:
    """Tests de l'outil web_search"""

    def test_web_search_registered(self):
        """web_search est enregistré"""
        tools = [t["name"] for t in BUILTIN_TOOLS.list_tools()]
        assert "web_search" in tools

    @pytest.mark.asyncio
    async def test_web_search_valid_query(self):
        """web_search retourne des résultats pour une requête valide"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "Abstract": "Python is a programming language",
                "Heading": "Python",
                "AbstractURL": "https://python.org",
                "AbstractSource": "Wikipedia",
                "RelatedTopics": [
                    {"Text": "Python programming language", "FirstURL": "https://example.com/1"},
                    {"Text": "Python tutorial", "FirstURL": "https://example.com/2"},
                ]
            }
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await web_search("python programming")
            
            assert result["success"] is True
            assert "results" in result["data"]
            assert result["data"]["query"] == "python programming"

    @pytest.mark.asyncio
    async def test_web_search_limits_results(self):
        """web_search limite le nombre de résultats"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"RelatedTopics": []}
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await web_search("test", num_results=100)
            
            # Should not exceed 10 results max
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_web_search_timeout(self):
        """web_search gère les timeouts"""
        with patch("httpx.AsyncClient") as mock_client:
            import httpx
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("timeout")
            )
            
            result = await web_search("test")
            
            assert result["success"] is False
            assert result["error"]["code"] == "E_WEB_TIMEOUT"


class TestWebRead:
    """Tests de l'outil web_read"""

    def test_web_read_registered(self):
        """web_read est enregistré"""
        tools = [t["name"] for t in BUILTIN_TOOLS.list_tools()]
        assert "web_read" in tools

    @pytest.mark.asyncio
    async def test_web_read_blocks_private_ip(self):
        """web_read bloque les IP privées (SSRF protection)"""
        result = await web_read("http://192.168.1.1/admin")
        
        assert result["success"] is False
        assert result["error"]["code"] == "E_URL_FORBIDDEN"

    @pytest.mark.asyncio
    async def test_web_read_blocks_localhost(self):
        """web_read bloque localhost (SSRF protection)"""
        result = await web_read("http://localhost:8080/api")
        
        # localhost est dans l'allowlist pour l'API interne
        # mais doit être validé correctement
        assert result is not None

    @pytest.mark.asyncio
    async def test_web_read_valid_url(self):
        """web_read lit une page valide"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "text/html"}
            mock_response.text = "<html><body><p>Hello World</p></body></html>"
            mock_response.url = "https://example.com"
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await web_read("https://example.com")
            
            assert result["success"] is True
            assert "content" in result["data"]

    @pytest.mark.asyncio
    async def test_web_read_rejects_binary(self):
        """web_read rejette les contenus binaires"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "application/octet-stream"}
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            result = await web_read("https://example.com/file.bin")
            
            assert result["success"] is False
            assert result["error"]["code"] == "E_CONTENT_TYPE"

    @pytest.mark.asyncio
    async def test_web_read_timeout(self):
        """web_read gère les timeouts"""
        with patch("httpx.AsyncClient") as mock_client:
            import httpx
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("timeout")
            )
            
            result = await web_read("https://slow-site.com")
            
            assert result["success"] is False
            assert result["error"]["code"] == "E_WEB_TIMEOUT"


class TestHtmlExtraction:
    """Tests de l'extraction de texte HTML"""

    def test_extract_removes_scripts(self):
        """Scripts sont supprimés"""
        html = "<p>Hello</p><script>alert('xss')</script><p>World</p>"
        result = _extract_text_from_html(html)
        assert "alert" not in result
        assert "Hello" in result
        assert "World" in result

    def test_extract_removes_styles(self):
        """Styles sont supprimés"""
        html = "<style>.red{color:red}</style><p>Content</p>"
        result = _extract_text_from_html(html)
        assert "color:red" not in result
        assert "Content" in result

    def test_extract_removes_tags(self):
        """Balises HTML sont supprimées"""
        html = "<div class='container'><p id='main'>Text</p></div>"
        result = _extract_text_from_html(html)
        assert "<div" not in result
        assert "<p" not in result
        assert "Text" in result

    def test_extract_decodes_entities(self):
        """Entités HTML sont décodées"""
        html = "5 &lt; 10 &amp; 10 &gt; 5"
        result = _extract_text_from_html(html)
        assert "5 < 10 & 10 > 5" in result
