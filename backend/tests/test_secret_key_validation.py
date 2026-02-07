"""
Tests pour CRQ-P0-6: SECRET_KEY obligatoire en production
Uses Settings(_env_file=None) to avoid .env file interference.
"""

import os

import pytest
from pydantic import ValidationError


class TestSecretKeyValidation:
    """Tests pour la validation SECRET_KEY obligatoire"""

    def test_secret_key_required_in_production(self, monkeypatch):
        """En production (TESTING=false), SECRET_KEY doit être fourni"""
        monkeypatch.delenv("SECRET_KEY", raising=False)
        monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
        monkeypatch.setenv("TESTING", "0")

        with pytest.raises(ValidationError) as exc_info:
            from app.core.config import Settings

            Settings(_env_file=None)

        error = str(exc_info.value)
        assert "SECRET_KEY is REQUIRED in production" in error

    def test_secret_key_provided_in_env(self, monkeypatch):
        """Si SECRET_KEY fourni dans env, config doit se charger"""
        monkeypatch.setenv("SECRET_KEY", "test_secret_key_very_long_string_for_jwt")
        monkeypatch.setenv("TESTING", "0")

        from app.core.config import Settings

        s = Settings(_env_file=None)

        assert s.SECRET_KEY == "test_secret_key_very_long_string_for_jwt"

    def test_jwt_secret_key_alias(self, monkeypatch):
        """JWT_SECRET_KEY doit fonctionner comme alias de SECRET_KEY"""
        monkeypatch.delenv("SECRET_KEY", raising=False)
        monkeypatch.setenv("JWT_SECRET_KEY", "jwt_secret_key_very_long_string")
        monkeypatch.setenv("TESTING", "0")

        from app.core.config import Settings

        s = Settings(_env_file=None)

        assert s.SECRET_KEY == "jwt_secret_key_very_long_string"

    def test_secret_key_generated_in_test_mode(self, monkeypatch):
        """En mode test (TESTING=true), SECRET_KEY peut être auto-généré"""
        monkeypatch.delenv("SECRET_KEY", raising=False)
        monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
        monkeypatch.setenv("TESTING", "1")

        from app.core.config import Settings

        s = Settings(_env_file=None)

        assert s.SECRET_KEY is not None
        assert len(s.SECRET_KEY) > 40

    def test_secret_key_from_env_overrides_default(self, monkeypatch):
        """SECRET_KEY depuis env doit avoir priorité sur génération"""
        custom_key = "my_custom_secret_key_from_env_file"
        monkeypatch.setenv("SECRET_KEY", custom_key)
        monkeypatch.setenv("TESTING", "1")

        from app.core.config import Settings

        s = Settings(_env_file=None)

        assert s.SECRET_KEY == custom_key

    def test_secret_key_error_message_helpful(self, monkeypatch):
        """Le message d'erreur doit être clair et donner la commande de génération"""
        monkeypatch.delenv("SECRET_KEY", raising=False)
        monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
        monkeypatch.setenv("TESTING", "0")

        with pytest.raises(ValidationError) as exc_info:
            from app.core.config import Settings

            Settings(_env_file=None)

        error = str(exc_info.value)
        assert "python3 -c 'import secrets" in error
        assert "JWT_SECRET_KEY or SECRET_KEY" in error
