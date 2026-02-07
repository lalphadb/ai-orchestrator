"""
Tests pour CRQ-P1-3: Strict CSP Headers (Content Security Policy)
"""

import pytest
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

from app.api.middleware import SecurityHeadersMiddleware
from app.core.config import settings


class TestStrictCSP:
    """Tests pour validation CSP strict vs legacy"""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup et restauration des settings"""
        original_enforce_strict_csp = settings.ENFORCE_STRICT_CSP
        yield
        settings.ENFORCE_STRICT_CSP = original_enforce_strict_csp

    @pytest.fixture
    def app_with_security_middleware(self):
        """App FastAPI minimaliste avec SecurityHeadersMiddleware"""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        return app

    def test_csp_legacy_mode_allows_unsafe_inline(self, app_with_security_middleware):
        """CSP legacy (flag OFF) doit autoriser unsafe-inline/unsafe-eval (backward compat)"""
        settings.ENFORCE_STRICT_CSP = False

        client = TestClient(app_with_security_middleware)
        response = client.get("/test")

        csp = response.headers.get("Content-Security-Policy", "")

        # Vérifier que unsafe-inline et unsafe-eval sont présents
        assert "'unsafe-inline'" in csp, "CSP legacy doit contenir 'unsafe-inline'"
        assert "'unsafe-eval'" in csp, "CSP legacy doit contenir 'unsafe-eval'"

    def test_csp_strict_mode_blocks_unsafe_inline(self, app_with_security_middleware):
        """CSP strict (flag ON) doit bloquer unsafe-inline/unsafe-eval (CRQ-P1-3)"""
        settings.ENFORCE_STRICT_CSP = True

        client = TestClient(app_with_security_middleware)
        response = client.get("/test")

        csp = response.headers.get("Content-Security-Policy", "")

        # Vérifier que unsafe-inline et unsafe-eval sont ABSENTS
        assert "'unsafe-inline'" not in csp, "CSP strict ne doit PAS contenir 'unsafe-inline'"
        assert "'unsafe-eval'" not in csp, "CSP strict ne doit PAS contenir 'unsafe-eval'"

    def test_csp_strict_allows_only_self_scripts(self, app_with_security_middleware):
        """CSP strict doit autoriser uniquement script-src 'self'"""
        settings.ENFORCE_STRICT_CSP = True

        client = TestClient(app_with_security_middleware)
        response = client.get("/test")

        csp = response.headers.get("Content-Security-Policy", "")

        # Vérifier script-src 'self' présent
        assert "script-src 'self'" in csp, "CSP strict doit contenir script-src 'self'"
        # Vérifier pas de unsafe-inline dans script-src
        assert "script-src 'self' 'unsafe-inline'" not in csp

    def test_csp_strict_allows_only_self_styles(self, app_with_security_middleware):
        """CSP strict doit autoriser uniquement style-src 'self'"""
        settings.ENFORCE_STRICT_CSP = True

        client = TestClient(app_with_security_middleware)
        response = client.get("/test")

        csp = response.headers.get("Content-Security-Policy", "")

        # Vérifier style-src 'self' présent
        assert "style-src 'self'" in csp, "CSP strict doit contenir style-src 'self'"
        # Vérifier pas de unsafe-inline dans style-src
        assert "style-src 'self' 'unsafe-inline'" not in csp

    def test_csp_strict_includes_base_uri_directive(self, app_with_security_middleware):
        """CSP strict doit inclure base-uri 'self' (protection <base>)"""
        settings.ENFORCE_STRICT_CSP = True

        client = TestClient(app_with_security_middleware)
        response = client.get("/test")

        csp = response.headers.get("Content-Security-Policy", "")

        # Vérifier base-uri présent
        assert "base-uri 'self'" in csp, "CSP strict doit contenir base-uri 'self'"

    def test_csp_strict_includes_form_action_directive(self, app_with_security_middleware):
        """CSP strict doit inclure form-action 'self' (protection formulaires)"""
        settings.ENFORCE_STRICT_CSP = True

        client = TestClient(app_with_security_middleware)
        response = client.get("/test")

        csp = response.headers.get("Content-Security-Policy", "")

        # Vérifier form-action présent
        assert "form-action 'self'" in csp, "CSP strict doit contenir form-action 'self'"

    def test_csp_legacy_no_base_uri_directive(self, app_with_security_middleware):
        """CSP legacy ne doit PAS avoir base-uri (backward compat)"""
        settings.ENFORCE_STRICT_CSP = False

        client = TestClient(app_with_security_middleware)
        response = client.get("/test")

        csp = response.headers.get("Content-Security-Policy", "")

        # Vérifier base-uri absent en mode legacy
        assert "base-uri" not in csp, "CSP legacy ne doit pas avoir base-uri (compat)"

    def test_csp_header_always_present(self, app_with_security_middleware):
        """CSP header doit toujours être présent (strict ou legacy)"""
        for enforce_strict in [True, False]:
            settings.ENFORCE_STRICT_CSP = enforce_strict

            client = TestClient(app_with_security_middleware)
            response = client.get("/test")

            assert (
                "Content-Security-Policy" in response.headers
            ), f"CSP header manquant (ENFORCE_STRICT_CSP={enforce_strict})"

    def test_csp_allows_websocket_connections(self, app_with_security_middleware):
        """CSP doit autoriser WebSocket (wss: et ws:) pour connect-src"""
        settings.ENFORCE_STRICT_CSP = True

        client = TestClient(app_with_security_middleware)
        response = client.get("/test")

        csp = response.headers.get("Content-Security-Policy", "")

        # Vérifier wss: et ws: présents dans connect-src
        assert (
            "connect-src 'self' wss: ws: https:" in csp
        ), "CSP doit autoriser WebSocket (wss: ws:)"

    def test_other_security_headers_present(self, app_with_security_middleware):
        """Vérifier que tous les headers de sécurité sont présents"""
        client = TestClient(app_with_security_middleware)
        response = client.get("/test")

        # Headers obligatoires
        assert "Strict-Transport-Security" in response.headers, "HSTS manquant"
        assert "X-Content-Type-Options" in response.headers, "X-Content-Type-Options manquant"
        assert "X-Frame-Options" in response.headers, "X-Frame-Options manquant"
        assert "X-XSS-Protection" in response.headers, "X-XSS-Protection manquant"
        assert "Referrer-Policy" in response.headers, "Referrer-Policy manquant"
        assert "Permissions-Policy" in response.headers, "Permissions-Policy manquant"

    def test_csp_frame_ancestors_none(self, app_with_security_middleware):
        """CSP doit bloquer tous les frames (frame-ancestors 'none')"""
        for enforce_strict in [True, False]:
            settings.ENFORCE_STRICT_CSP = enforce_strict

            client = TestClient(app_with_security_middleware)
            response = client.get("/test")

            csp = response.headers.get("Content-Security-Policy", "")
            assert (
                "frame-ancestors 'none'" in csp
            ), "CSP doit contenir frame-ancestors 'none' (anti-clickjacking)"

    def test_csp_default_src_self(self, app_with_security_middleware):
        """CSP doit avoir default-src 'self' comme fallback"""
        for enforce_strict in [True, False]:
            settings.ENFORCE_STRICT_CSP = enforce_strict

            client = TestClient(app_with_security_middleware)
            response = client.get("/test")

            csp = response.headers.get("Content-Security-Policy", "")
            assert "default-src 'self'" in csp, "CSP doit avoir default-src 'self' comme fallback"
