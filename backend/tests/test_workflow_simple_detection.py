"""
Tests for simple request detection - Prevent RUNNING bug regression

Bug Fix: https://github.com/anthropics/ai-orchestrator/issues/XXX
Date: 2026-01-12

Ensures system info queries use fast path (skip SPEC/PLAN phases) to prevent
client-side timeouts when backend takes too long.
"""

import pytest

from app.services.react_engine.workflow_engine import workflow_engine


class TestSimpleRequestDetection:
    """Test _is_simple_request() method for performance-critical queries"""

    # System info queries (should be SIMPLE → fast path)
    # Note: Queries need "?" or question words to be safe
    SYSTEM_INFO_QUERIES = [
        # French - with question marks
        "uptime du serveur?",
        "quel est l'état du système?",
        "quels modèles sont disponibles?",
        "status du serveur?",
        "memory usage?",
        "disk space?",
        "quelle version?",
        # French - with "affiche", "montre", "liste" + question words
        "affiche les infos CPU?",
        "montre la version?",
        "liste les modèles?",
        # English - with question marks
        "server uptime?",
        "what is the system status?",
        "system status?",
        "memory info?",
        "disk info?",
        # English - with "show", "display", "list"
        "show CPU info?",
        "display version?",
        "list available models?",
    ]

    # Complex queries (should be COMPLEX → full workflow)
    COMPLEX_QUERIES = [
        "crée un fichier test.txt avec le contenu 'hello'",
        "modifie le fichier config.yml",
        "supprime le dossier /tmp/test",
        "install docker",
        "update the system",
        "create a new user",
    ]

    @pytest.mark.parametrize("query", SYSTEM_INFO_QUERIES)
    def test_system_info_queries_are_simple(self, query):
        """System info queries should be classified as SIMPLE for fast path"""
        # This test prevents regression of the RUNNING bug
        # by ensuring system queries don't require SPEC/PLAN phases
        result = workflow_engine._is_simple_request(query)
        assert result is True, (
            f"Query '{query}' should be SIMPLE but was classified as COMPLEX. "
            f"This will cause slow execution and potential client timeouts."
        )

    @pytest.mark.parametrize("query", COMPLEX_QUERIES)
    def test_complex_queries_are_complex(self, query):
        """Action queries should be classified as COMPLEX for safety"""
        result = workflow_engine._is_simple_request(query)
        assert result is False, (
            f"Query '{query}' should be COMPLEX but was classified as SIMPLE. "
            f"This could bypass necessary SPEC/PLAN safety checks."
        )

    def test_conversational_queries_are_simple(self):
        """Conversational queries should be SIMPLE"""
        simple_queries = [
            "bonjour",
            "hello",
            "merci",
            "thanks",
            "comment ça va?",
            "who are you?",
        ]
        for query in simple_queries:
            result = workflow_engine._is_simple_request(query)
            assert result is True, f"Conversational query '{query}' should be SIMPLE"

    def test_regression_uptime_query(self):
        """Regression test for original bug: 'uptime du serveur?' must be SIMPLE"""
        # This was the exact query that triggered the bug
        result = workflow_engine._is_simple_request("uptime du serveur?")
        assert result is True, (
            "REGRESSION: 'uptime du serveur?' is COMPLEX again! "
            "This will cause the RUNNING bug to reappear."
        )

    def test_regression_models_query(self):
        """Regression test: 'Quels modèles LLM sont disponibles?' must be SIMPLE"""
        # This is the second test case from the bug report
        result = workflow_engine._is_simple_request("Quels modèles LLM sont disponibles?")
        assert result is True, (
            "REGRESSION: Model list query is COMPLEX again! " "This will cause slow response times."
        )
