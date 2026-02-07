"""
Tests pour CRQ-P0-4: Migration token HttpOnly
Test la fonction extract_token_from_request avec cookies et headers
"""

from unittest.mock import Mock

import pytest
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.security import extract_token_from_request


class TestHttpOnlyCookies:
    """Tests pour l'extraction de tokens depuis cookies HttpOnly"""

    def test_extract_from_cookie_when_enabled(self, monkeypatch):
        """Doit extraire le token depuis le cookie si USE_HTTPONLY_COOKIES=true"""
        monkeypatch.setattr(settings, "USE_HTTPONLY_COOKIES", True)

        # Mock request avec cookie
        request = Mock(spec=Request)
        request.cookies = {"access_token": "token_from_cookie"}

        token = extract_token_from_request(request, credentials=None)
        assert token == "token_from_cookie"

    def test_extract_from_header_when_cookies_disabled(self, monkeypatch):
        """Doit extraire le token depuis le header si USE_HTTPONLY_COOKIES=false"""
        monkeypatch.setattr(settings, "USE_HTTPONLY_COOKIES", False)

        # Mock request avec cookie (ignoré)
        request = Mock(spec=Request)
        request.cookies = {"access_token": "token_from_cookie"}

        # Mock credentials header
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token_from_header")

        token = extract_token_from_request(request, credentials)
        assert token == "token_from_header"

    def test_fallback_to_header_when_no_cookie(self, monkeypatch):
        """Doit fallback sur header si cookie absent (backward compatibility)"""
        monkeypatch.setattr(settings, "USE_HTTPONLY_COOKIES", True)

        # Mock request sans cookie
        request = Mock(spec=Request)
        request.cookies = {}

        # Mock credentials header
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token_from_header")

        token = extract_token_from_request(request, credentials)
        # Backward compat: fallback sur header si cookie absent
        assert token == "token_from_header"

    def test_cookie_priority_over_header(self, monkeypatch):
        """Le cookie doit avoir la priorité sur le header si cookies activés"""
        monkeypatch.setattr(settings, "USE_HTTPONLY_COOKIES", True)

        # Mock request avec cookie
        request = Mock(spec=Request)
        request.cookies = {"access_token": "token_from_cookie"}

        # Mock credentials header (sera ignoré)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token_from_header")

        token = extract_token_from_request(request, credentials)
        assert token == "token_from_cookie"

    def test_no_token_available(self, monkeypatch):
        """Doit retourner None si aucun token disponible"""
        monkeypatch.setattr(settings, "USE_HTTPONLY_COOKIES", False)

        # Mock request sans cookie
        request = Mock(spec=Request)
        request.cookies = {}

        token = extract_token_from_request(request, credentials=None)
        assert token is None

    def test_backward_compatibility_header_only(self, monkeypatch):
        """Mode legacy: header auth doit continuer à fonctionner"""
        monkeypatch.setattr(settings, "USE_HTTPONLY_COOKIES", False)

        request = Mock(spec=Request)
        request.cookies = {}

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="legacy_token")

        token = extract_token_from_request(request, credentials)
        assert token == "legacy_token"
