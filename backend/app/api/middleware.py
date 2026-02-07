"""
Middlewares pour l'application AI Orchestrator v7.1

- RequestTracingMiddleware: Ajoute request_id à toutes les requêtes
- Logs structurés pour chaque requête entrante/sortante
"""

import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour tracer les requêtes avec un request_id unique.

    Fonctionnalités:
    - Génère ou récupère request_id depuis header X-Request-ID
    - Stocke request_id dans request.state (accessible dans routes)
    - Ajoute request_id dans les headers de réponse
    - Log entrée/sortie de chaque requête avec durée

    Example headers:
        Request:  X-Request-ID: abc123 (optionnel)
        Response: X-Request-ID: abc123 (toujours présent)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        from app.core.config import settings

        # Générer ou récupérer request_id
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # CRQ-P1-6: Générer ou récupérer correlation_id pour traçabilité distribuée
        correlation_id = None
        if settings.ENABLE_CORRELATION_ID:
            correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
            request.state.correlation_id = correlation_id

        # Stocker dans request.state pour accès dans routes
        request.state.request_id = request_id

        # Timing
        start_time = time.time()

        # Logger la requête entrante (CRQ-P1-6: avec correlation_id si activé)
        log_extra = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params) if request.query_params else None,
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
        if correlation_id:
            log_extra["correlation_id"] = correlation_id

        logger.info("Request started", extra=log_extra)

        # Exécuter la requête
        try:
            response = await call_next(request)
        except Exception as e:
            # Logger l'erreur avec request_id (CRQ-P1-6: et correlation_id si activé)
            duration_ms = (time.time() - start_time) * 1000
            error_extra = {
                "request_id": request_id,
                "duration_ms": round(duration_ms, 2),
                "error_type": type(e).__name__,
            }
            if correlation_id:
                error_extra["correlation_id"] = correlation_id

            logger.error(
                f"Request failed: {type(e).__name__}: {str(e)}",
                extra=error_extra,
            )
            raise

        # Ajouter request_id à la réponse
        response.headers["X-Request-ID"] = request_id

        # CRQ-P1-6: Ajouter correlation_id dans la réponse si activé
        if correlation_id:
            response.headers["X-Correlation-ID"] = correlation_id

        # Calculer durée
        duration_ms = (time.time() - start_time) * 1000

        # Logger la réponse (CRQ-P1-6: avec correlation_id si activé)
        complete_extra = {
            "request_id": request_id,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        }
        if correlation_id:
            complete_extra["correlation_id"] = correlation_id

        logger.info("Request completed", extra=complete_extra)

        return response


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour monitorer les performances et identifier les requêtes lentes.

    Logs un WARNING si une requête prend plus de threshold_ms.
    """

    def __init__(self, app, threshold_ms: int = 5000):
        super().__init__(app)
        self.threshold_ms = threshold_ms

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Exécuter la requête
        response = await call_next(request)

        # Calculer durée
        duration_ms = (time.time() - start_time) * 1000

        # Logger si lent
        if duration_ms > self.threshold_ms:
            request_id = getattr(request.state, "request_id", "unknown")
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "duration_ms": round(duration_ms, 2),
                    "threshold_ms": self.threshold_ms,
                    "method": request.method,
                    "path": request.url.path,
                },
            )

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour ajouter les headers de sécurité (OWASP).

    Headers ajoutés:
    - Strict-Transport-Security (HSTS)
    - X-Content-Type-Options
    - X-Frame-Options
    - X-XSS-Protection
    - Content-Security-Policy
    - Referrer-Policy
    - Permissions-Policy
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        from app.core.config import settings

        response = await call_next(request)

        # HSTS - Force HTTPS pendant 1 an
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Empêche le sniffing MIME
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Protection clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Protection XSS legacy (navigateurs anciens)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # CSP - Content Security Policy (CRQ-P1-3)
        if settings.ENFORCE_STRICT_CSP:
            # CSP strict: pas de unsafe-inline/unsafe-eval
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' wss: ws: https:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
        else:
            # CSP legacy (backward compat): unsafe-inline/unsafe-eval autorisés
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' wss: ws: https:; "
                "frame-ancestors 'none';"
            )

        # Contrôle du Referrer
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (anciennes Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), " "microphone=(), " "camera=(), " "payment=()"
        )

        return response


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour instrumenter les requêtes HTTP avec Prometheus.

    Métriques collectées:
    - ai_orchestrator_requests_total: Compteur par endpoint/method/status
    - ai_orchestrator_request_duration_seconds: Histogramme de latence
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        from app.core.metrics import (HTTP_REQUEST_DURATION,
                                      HTTP_REQUESTS_TOTAL, REQUEST_DURATION,
                                      REQUESTS_TOTAL)

        # Ignorer /metrics et /health pour éviter pollution
        if request.url.path in ["/metrics", "/health"]:
            return await call_next(request)

        start_time = time.time()

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise e
        finally:
            duration = time.time() - start_time

            # Simplifier le path pour éviter explosion de cardinalité
            path = request.url.path
            # Normaliser les IDs dans les paths
            import re

            path = re.sub(r"/[0-9a-f-]{36}", "/{id}", path)  # UUIDs
            path = re.sub(r"/\d+", "/{id}", path)  # IDs numériques

            # Enregistrer métriques (nom personnalisé)
            REQUESTS_TOTAL.labels(
                endpoint=path, method=request.method, status=str(status_code)
            ).inc()
            REQUEST_DURATION.labels(endpoint=path).observe(duration)

            # Enregistrer métriques (nom standard pour Grafana)
            HTTP_REQUESTS_TOTAL.labels(
                endpoint=path, method=request.method, status_code=str(status_code)
            ).inc()
            HTTP_REQUEST_DURATION.labels(endpoint=path, method=request.method).observe(duration)

        return response
