"""
Tests pour CRQ-P1-6: Correlation ID pour traçabilité distribuée
"""

import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.middleware import RequestTracingMiddleware
from app.core.config import settings
from app.models.ws_events import WSThinkingEvent


class TestCorrelationID:
    """Tests pour validation correlation_id dans HTTP et WebSocket"""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup et restauration des settings"""
        original_enable_correlation_id = settings.ENABLE_CORRELATION_ID
        yield
        settings.ENABLE_CORRELATION_ID = original_enable_correlation_id

    def _create_test_app(self):
        """Créer une app test avec middleware (appelée après modification settings)"""
        from fastapi import Request

        app = FastAPI()
        app.add_middleware(RequestTracingMiddleware)

        @app.get("/test")
        async def test_endpoint(request: Request):
            # Retourner correlation_id si présent dans request.state
            correlation_id = getattr(request.state, "correlation_id", None)
            return {"status": "ok", "correlation_id": correlation_id}

        return app

    def test_correlation_id_generated_when_enabled(self):
        """Correlation ID doit être généré automatiquement si flag ON et header absent"""
        settings.ENABLE_CORRELATION_ID = True
        app = self._create_test_app()

        client = TestClient(app)
        response = client.get("/test")

        # Vérifier présence dans header réponse
        assert (
            "X-Correlation-ID" in response.headers
        ), "Correlation ID doit être présent dans réponse (flag ON)"

        # Vérifier UUID valide
        correlation_id = response.headers["X-Correlation-ID"]
        try:
            uuid.UUID(correlation_id)
        except ValueError:
            pytest.fail(f"Correlation ID invalide (pas UUID): {correlation_id}")

        # Vérifier propagation dans request.state
        assert (
            response.json()["correlation_id"] == correlation_id
        ), "Correlation ID doit être propagé dans request.state"

    def test_correlation_id_preserved_from_header(self):
        """Correlation ID fourni dans header doit être préservé"""
        settings.ENABLE_CORRELATION_ID = True
        app = self._create_test_app()

        custom_correlation_id = "custom-trace-123"
        client = TestClient(app)
        response = client.get("/test", headers={"X-Correlation-ID": custom_correlation_id})

        # Vérifier préservation du correlation_id custom
        assert (
            response.headers["X-Correlation-ID"] == custom_correlation_id
        ), "Correlation ID custom doit être préservé"

        # Vérifier propagation dans request.state
        assert response.json()["correlation_id"] == custom_correlation_id

    def test_correlation_id_absent_when_disabled(self):
        """Correlation ID doit être absent si flag OFF (backward compat)"""
        settings.ENABLE_CORRELATION_ID = False
        app = self._create_test_app()

        client = TestClient(app)
        response = client.get("/test")

        # Vérifier absence dans header réponse
        assert (
            "X-Correlation-ID" not in response.headers
        ), "Correlation ID ne doit PAS être présent (flag OFF)"

        # Vérifier absence dans request.state
        assert (
            response.json()["correlation_id"] is None
        ), "Correlation ID ne doit PAS être dans request.state (flag OFF)"

    def test_correlation_id_ignored_when_disabled(self):
        """Header X-Correlation-ID doit être ignoré si flag OFF"""
        settings.ENABLE_CORRELATION_ID = False
        app = self._create_test_app()

        custom_correlation_id = "should-be-ignored"
        client = TestClient(app)
        response = client.get("/test", headers={"X-Correlation-ID": custom_correlation_id})

        # Vérifier absence dans réponse (ignoré)
        assert (
            "X-Correlation-ID" not in response.headers
        ), "Correlation ID fourni doit être ignoré (flag OFF)"

    def test_request_id_still_present(self):
        """Request ID doit toujours être présent (orthogonal à correlation_id)"""
        for enable_correlation in [True, False]:
            settings.ENABLE_CORRELATION_ID = enable_correlation
            app = self._create_test_app()

            client = TestClient(app)
            response = client.get("/test")

            # Request ID toujours présent
            assert (
                "X-Request-ID" in response.headers
            ), f"Request ID doit être présent (ENABLE_CORRELATION_ID={enable_correlation})"


class TestCorrelationIDInWebSocketEvents:
    """Tests pour propagation correlation_id dans events WebSocket"""

    def test_ws_event_accepts_correlation_id(self):
        """WSEventBase doit accepter correlation_id optionnel (CRQ-P1-6)"""
        event = WSThinkingEvent(
            run_id="test-run-123", correlation_id="trace-abc", data={"message": "Test thinking"}
        )

        assert (
            event.correlation_id == "trace-abc"
        ), "Correlation ID doit être accepté dans WSEventBase"

    def test_ws_event_correlation_id_optional(self):
        """Correlation ID doit être optionnel dans WSEventBase (backward compat)"""
        event = WSThinkingEvent(run_id="test-run-123", data={"message": "Test thinking"})

        assert (
            event.correlation_id is None
        ), "Correlation ID doit être None si non fourni (backward compat)"

    def test_ws_event_serialization_includes_correlation_id(self):
        """Serialization JSON doit inclure correlation_id si présent"""
        event = WSThinkingEvent(
            run_id="test-run-123", correlation_id="trace-xyz", data={"message": "Test"}
        )

        event_dict = event.model_dump()

        assert "correlation_id" in event_dict, "Serialization doit inclure correlation_id"
        assert event_dict["correlation_id"] == "trace-xyz"

    def test_ws_event_serialization_without_correlation_id(self):
        """Serialization JSON doit exclure correlation_id si None (backward compat)"""
        event = WSThinkingEvent(run_id="test-run-123", data={"message": "Test"})

        event_dict = event.model_dump(exclude_none=True)

        # correlation_id ne doit pas apparaître si None (backward compat)
        assert (
            "correlation_id" not in event_dict or event_dict["correlation_id"] is None
        ), "correlation_id=None ne doit pas apparaître en JSON (backward compat)"
