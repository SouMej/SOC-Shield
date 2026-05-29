"""
Rule Engine — Executes detection rules against event batches.
"""
import logging
from typing import Optional
from detection_rules.rules.brute_force import BruteForceRule, PasswordSprayRule
from detection_rules.rules.priv_escalation import PrivilegeEscalationRule
from detection_rules.rules.lateral_movement import LateralMovementRule
from detection_rules.rules.powershell_abuse import PowerShellAbuseRule
from detection_rules.rules.kerberoasting import KerberoastingRule
from detection_rules.rules.persistence import PersistenceRule

logger = logging.getLogger(__name__)


class RuleMatch:
    """Represents a detection rule match."""
    def __init__(self, rule_name: str, severity: str, threat_score: int,
                 attack_type: str, description: str, mitre_techniques: list[str],
                 matched_events: list[dict], hostname: str = "", user: str = "",
                 source_ip: str = ""):
        self.rule_name = rule_name
        self.severity = severity
        self.threat_score = threat_score
        self.attack_type = attack_type
        self.description = description
        self.mitre_techniques = mitre_techniques
        self.matched_events = matched_events
        self.hostname = hostname
        self.user = user
        self.source_ip = source_ip

    def to_alert_dict(self) -> dict:
        return {
            "rule_name": self.rule_name,
            "severity": self.severity,
            "threat_score": self.threat_score,
            "attack_type": self.attack_type,
            "explanation": self.description,
            "mitre_techniques": self.mitre_techniques,
            "hostname": self.hostname,
            "target_user": self.user,
            "source_ip": self.source_ip,
            "related_events": len(self.matched_events),
            "ai_analysis": False,
        }


class RuleEngine:
    """Manages and executes all detection rules."""

    def __init__(self):
        self.rules = [
            BruteForceRule(),
            PasswordSprayRule(),
            PrivilegeEscalationRule(),
            LateralMovementRule(),
            PowerShellAbuseRule(),
            KerberoastingRule(),
            PersistenceRule(),
        ]
        logger.info(f"Rule engine initialized with {len(self.rules)} rules")

    def evaluate_batch(self, events: list[dict]) -> list[RuleMatch]:
        """Run all rules against an event batch."""
        matches = []
        for rule in self.rules:
            try:
                result = rule.evaluate(events)
                if result:
                    if isinstance(result, list):
                        matches.extend(result)
                    else:
                        matches.append(result)
            except Exception as e:
                logger.error(f"Rule {rule.name} error: {e}")
        return matches


rule_engine = RuleEngine()
