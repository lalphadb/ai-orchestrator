"""
Contrats I/O pour les outils - Validation standardisée
"""

from typing import Any

# Codes d'erreur standardisés
RECOVERABLE_ERRORS = {
    "E_FILE_NOT_FOUND",
    "E_DIR_NOT_FOUND",
    "E_PATH_NOT_FOUND",
}

FATAL_ERRORS = {
    "E_PERMISSION",
    "E_CMD_NOT_ALLOWED",
    "E_NOT_ALLOWED",  # execute_command role-based denial
    "E_PARSE_ERROR",  # Command parsing/validation errors
    "E_PATH_FORBIDDEN",
    "E_VALIDATION",
    "E_EXECUTION",
    "E_TOOL_EXEC",  # Tool execution wrapper errors
    "E_OLLAMA_ERROR",  # Ollama API errors
    "E_SEARCH_ERROR",  # search_files errors
    "E_INVALID_TARGET",  # run_tests/run_lint invalid target
    "E_URL_FORBIDDEN",  # http_request SSRF blocked
    "E_HTTP_TIMEOUT",  # http_request timeout
    "E_HTTP_METHOD",  # http_request unsupported method
    "E_HTTP_ERROR",  # http_request general errors
    "E_IMPORT",  # Missing dependency
    "E_GOVERNANCE_DENIED",  # Governance blocked action (no justification)
}

NETWORK_ERRORS = {
    "E_NETWORK_ERROR",
    "E_TIMEOUT",
    "E_DNS_ERROR",
}

ALL_ERROR_CODES = RECOVERABLE_ERRORS | FATAL_ERRORS | NETWORK_ERRORS


def validate_tool_result(result: dict[str, Any]) -> tuple[bool, str]:
    """
    Valide qu'un résultat d'outil respecte le contrat I/O standard.

    Args:
        result: Dictionnaire retourné par un outil

    Returns:
        (is_valid, error_message)
    """
    # Vérifier les clés requises
    required_keys = {"success", "data", "error", "meta"}
    if not all(key in result for key in required_keys):
        missing = required_keys - set(result.keys())
        return False, f"Missing required keys: {missing}"

    # Vérifier les types
    if not isinstance(result["success"], bool):
        return False, f"'success' must be bool, got {type(result['success'])}"

    if result["data"] is not None and not isinstance(result["data"], dict):
        return False, f"'data' must be dict or None, got {type(result['data'])}"

    if result["error"] is not None and not isinstance(result["error"], dict):
        return False, f"'error' must be dict or None, got {type(result['error'])}"

    if not isinstance(result["meta"], dict):
        return False, f"'meta' must be dict, got {type(result['meta'])}"

    # Vérifier la cohérence success=True
    if result["success"]:
        if result["data"] is None:
            return False, "success=True requires data to be non-None"
        if result["error"] is not None:
            return False, "success=True requires error to be None"

    # Vérifier la cohérence success=False
    if not result["success"]:
        if result["data"] is not None:
            return False, "success=False requires data to be None"
        if result["error"] is None:
            return False, "success=False requires error to be non-None"

        # Vérifier la structure de error
        error_required = {"code", "message", "recoverable"}
        if not all(key in result["error"] for key in error_required):
            missing = error_required - set(result["error"].keys())
            return False, f"error missing keys: {missing}"

        if not isinstance(result["error"]["recoverable"], bool):
            return False, "error.recoverable must be bool"

        # Vérifier que le code d'erreur est connu
        error_code = result["error"]["code"]
        if error_code not in ALL_ERROR_CODES:
            return (
                False,
                f"Unknown error code: {error_code}. " f"Expected one of: {sorted(ALL_ERROR_CODES)}",
            )

    # Vérifier meta
    if "duration_ms" not in result["meta"]:
        return False, "meta must contain 'duration_ms'"

    return True, ""


def assert_tool_success(result: dict[str, Any], expected_keys: set[str] | None = None):
    """
    Assert qu'un résultat d'outil est un succès valide.

    Args:
        result: Résultat de l'outil
        expected_keys: Clés attendues dans data (optionnel)
    """
    is_valid, error = validate_tool_result(result)
    assert is_valid, f"Invalid tool result: {error}"

    assert result["success"], f"Expected success=True, got error: {result.get('error')}"

    if expected_keys:
        missing = expected_keys - set(result["data"].keys())
        assert not missing, f"Missing expected keys in data: {missing}"


def assert_tool_error(
    result: dict[str, Any], expected_code: str, should_be_recoverable: bool | None = None
):
    """
    Assert qu'un résultat d'outil est une erreur valide.

    Args:
        result: Résultat de l'outil
        expected_code: Code d'erreur attendu
        should_be_recoverable: Si spécifié, vérifie que recoverable correspond
    """
    is_valid, error = validate_tool_result(result)
    assert is_valid, f"Invalid tool result: {error}"

    assert not result["success"], "Expected success=False"
    assert result["error"]["code"] == expected_code, (
        f"Expected error code {expected_code}, " f"got {result['error']['code']}"
    )

    if should_be_recoverable is not None:
        assert result["error"]["recoverable"] == should_be_recoverable, (
            f"Expected recoverable={should_be_recoverable}, "
            f"got {result['error']['recoverable']}"
        )


def assert_response_time(result: dict[str, Any], max_ms: int):
    """
    Assert que le temps de réponse est acceptable.

    Args:
        result: Résultat de l'outil
        max_ms: Temps maximum en millisecondes
    """
    duration = result["meta"].get("duration_ms", 0)
    assert duration <= max_ms, f"Response too slow: {duration}ms > {max_ms}ms"
