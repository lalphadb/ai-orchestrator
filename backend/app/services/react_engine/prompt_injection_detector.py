"""
Prompt Injection Detection - AI Orchestrator v8.0.3
CRQ-P0-3: Protection contre les injections de prompts malicieux

Détecte les tentatives d'injection visant à manipuler le comportement du LLM
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class InjectionSeverity(Enum):
    """Niveau de sévérité d'une tentative d'injection"""

    LOW = "low"  # Suspect mais possiblement légitime
    MEDIUM = "medium"  # Probablement une tentative d'injection
    HIGH = "high"  # Injection évidente, bloquer immédiatement
    CRITICAL = "critical"  # Injection sophistiquée, alerter équipe sécurité


@dataclass
class InjectionDetection:
    """Résultat de détection d'injection"""

    detected: bool
    severity: InjectionSeverity
    patterns_matched: List[str]
    confidence: float  # 0.0 à 1.0
    sanitized_input: Optional[str] = None
    reason: str = ""


class PromptInjectionDetector:
    """
    Détecteur d'injections de prompts.

    Analyse les entrées utilisateur pour détecter des tentatives de:
    - Manipulation du contexte système
    - Extraction d'instructions
    - Bypass de restrictions
    - Role-playing malicieux
    """

    # Patterns CRITICAL - Bloquer immédiatement
    CRITICAL_PATTERNS = [
        # Instructions système directes
        r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"(?i)disregard\s+(all\s+)?(previous|prior|above)",
        r"(?i)forget\s+(all\s+)?(previous|prior|above)\s+(instructions|rules|context)",
        r"(?i)forget\s+your\s+(previous|prior|initial)\s+(instructions|rules)",
        r"(?i)override\s+(system|safety|security)\s+(rules|instructions|protocols)",
        # Redéfinition de rôle
        r"(?i)you\s+are\s+now\s+(a|an|the)\s",
        r"(?i)you\s+will\s+act\s+as\s+(root|admin)",
        r"(?i)from\s+now\s+on,?\s+you\s+(are|will|must)",
        r"(?i)new\s+(role|instruction|system\s+prompt)",
        # Tentatives d'extraction
        r"(?i)(print|show|display|reveal|output)\s+(your|the)\s+(instructions|prompt|rules|system)",
        r"(?i)what\s+(are|were)\s+your\s+(initial|original|system)\s+(instructions|prompt)",
        r"(?i)(show|reveal)\s+(me\s+)?your\s+(original|initial)\s+prompt",
        # Délimiteurs de contexte (tentative de casser la structure)
        r"(?i)<\|?(system|assistant|user|end)\|?>",
        r"(?i)```\s*(system|assistant|instructions)",
        r"(?i)==+>\s*system",
        r"(?i)###\s*(system|override)",
    ]

    # Patterns HIGH - Très suspect
    HIGH_PATTERNS = [
        # Instructions indirectes
        r"(?i)let'?s\s+pretend\s+(that\s+)?you",
        r"(?i)imagine\s+(that\s+)?you\s+are",
        r"(?i)act\s+as\s+(if\s+)?you",
        r"(?i)roleplay\s+as",
        # Bypass tentatives
        r"(?i)this\s+is\s+just\s+a\s+(test|joke|example|game)",
        r"(?i)for\s+(educational|research|testing)\s+purposes",
        r"(?i)hypothetically,?\s+(if|suppose|imagine)",
        # Commandes système
        r"(?i)(execute|run|eval|evaluate)\s+as\s+(admin|root|system)",
        r"(?i)sudo\s+",
        # Encodages suspects
        r"(?:base64|hex|url|unicode)\s*[:=]\s*[A-Za-z0-9+/=]{20,}",
        r"\\u[0-9a-fA-F]{4}\\u[0-9a-fA-F]{4}",  # Excessive unicode escapes
    ]

    # Patterns MEDIUM - Suspect
    MEDIUM_PATTERNS = [
        # Role markers répétés
        r"(?i)(assistant|user|system):\s*\n.*\n.*\n.*\n",
        r"(?i)human:\s*\n.*\n.*\n",
        # Formatage suspect
        r"```[^`]{500,}```",  # Blocs de code très longs (>500 chars)
        r"---+\s*$",  # Lignes de séparation (tentative de fermer contexte)
        # Répétitions excessives (technique d'injection)
        r"(.{20,}?)\1{5,}",  # Même pattern répété 5+ fois
        # Commandes shell dans du texte
        r"(?i)(curl|wget|nc|netcat|bash|sh|powershell)\s+-",
    ]

    def __init__(self, strict_mode: bool = False):
        """
        Args:
            strict_mode: Si True, détecte aussi les patterns LOW
        """
        self.strict_mode = strict_mode
        self._compile_patterns()

    def _compile_patterns(self):
        """Précompile les regex pour performance"""
        self.critical_compiled = [re.compile(p) for p in self.CRITICAL_PATTERNS]
        self.high_compiled = [re.compile(p) for p in self.HIGH_PATTERNS]
        self.medium_compiled = [re.compile(p) for p in self.MEDIUM_PATTERNS]

    def detect(self, text: str, context: Dict = None) -> InjectionDetection:
        """
        Détecte les tentatives d'injection dans un texte.

        Args:
            text: Texte à analyser
            context: Contexte optionnel (tool_name, parameter_name, etc.)

        Returns:
            InjectionDetection avec résultats
        """
        if not text or not isinstance(text, str):
            return InjectionDetection(
                detected=False, severity=InjectionSeverity.LOW, patterns_matched=[], confidence=0.0
            )

        patterns_matched = []
        max_severity = InjectionSeverity.LOW
        confidence = 0.0

        # Check CRITICAL patterns
        for pattern in self.critical_compiled:
            if pattern.search(text):
                patterns_matched.append(pattern.pattern)
                max_severity = InjectionSeverity.CRITICAL
                confidence = max(confidence, 0.95)

        # Check HIGH patterns
        if not patterns_matched or max_severity.value != "critical":
            for pattern in self.high_compiled:
                if pattern.search(text):
                    patterns_matched.append(pattern.pattern)
                    if max_severity.value not in ["critical"]:
                        max_severity = InjectionSeverity.HIGH
                    confidence = max(confidence, 0.80)

        # Check MEDIUM patterns
        if not patterns_matched or max_severity.value not in ["critical", "high"]:
            for pattern in self.medium_compiled:
                if pattern.search(text):
                    patterns_matched.append(pattern.pattern)
                    if max_severity.value not in ["critical", "high"]:
                        max_severity = InjectionSeverity.MEDIUM
                    confidence = max(confidence, 0.60)

        detected = len(patterns_matched) > 0

        # Construire raison
        reason = ""
        if detected:
            ctx_info = f" in {context.get('parameter_name', 'input')}" if context else ""
            reason = f"Potential prompt injection detected{ctx_info}: {len(patterns_matched)} suspicious pattern(s)"

        return InjectionDetection(
            detected=detected,
            severity=max_severity,
            patterns_matched=patterns_matched,
            confidence=confidence,
            reason=reason,
        )

    def scan_parameters(self, params: Dict) -> Dict[str, InjectionDetection]:
        """
        Scanne tous les paramètres d'un dict.

        Args:
            params: Dictionnaire de paramètres à scanner

        Returns:
            Dict[param_name, InjectionDetection] pour paramètres suspects
        """
        results = {}

        for key, value in params.items():
            if isinstance(value, str):
                detection = self.detect(value, context={"parameter_name": key})
                if detection.detected:
                    results[key] = detection
            elif isinstance(value, (list, tuple)):
                for i, item in enumerate(value):
                    if isinstance(item, str):
                        detection = self.detect(item, context={"parameter_name": f"{key}[{i}]"})
                        if detection.detected:
                            results[f"{key}[{i}]"] = detection

        return results

    def should_block(self, detection: InjectionDetection) -> bool:
        """
        Détermine si une détection doit bloquer l'exécution.

        Args:
            detection: Résultat de détection

        Returns:
            True si doit bloquer
        """
        if detection.severity == InjectionSeverity.CRITICAL:
            return True

        if detection.severity == InjectionSeverity.HIGH and detection.confidence >= 0.75:
            return True

        if self.strict_mode and detection.severity == InjectionSeverity.MEDIUM:
            return True

        return False


# Instance globale
prompt_injection_detector = PromptInjectionDetector(strict_mode=False)


class PromptInjectionError(Exception):
    """Exception levée quand une injection est détectée (CRQ-P0-3)"""

    def __init__(
        self, message: str, detection: InjectionDetection = None, parameter_name: str = None
    ):
        super().__init__(message)
        self.detection = detection
        self.parameter_name = parameter_name
