"""
Persistence Detection Rule
"""


class PersistenceRule:
    """Detects persistence mechanisms: new services, scheduled tasks."""
    name = "Persistence Detection"

    SUSPICIOUS_SERVICE_NAMES = [
        "suspicious", "backdoor", "shell", "reverse", "beacon",
        "payload", "implant", "meterpreter", "cobalt",
    ]

    def evaluate(self, events):
        service_events = [e for e in events if e.get("event_id") == 7045]
        if not service_events:
            return None

        from detection_rules.rule_engine import RuleMatch
        suspicious = []
        for e in service_events:
            msg = (e.get("message") or "").lower()
            if any(s in msg for s in self.SUSPICIOUS_SERVICE_NAMES):
                suspicious.append(e)

        if suspicious:
            return RuleMatch(
                rule_name=self.name, severity="HIGH", threat_score=80,
                attack_type="Persistence",
                description=f"{len(suspicious)} suspicious service installations detected",
                mitre_techniques=["T1543.003"],
                matched_events=suspicious,
                hostname=suspicious[0].get("hostname", ""),
            )

        # Flag any service creation in a batch with other suspicious activity
        has_suspicious = any(
            e.get("event_category") in ("authentication_failure", "privilege_escalation")
            for e in events
        )
        if has_suspicious and service_events:
            return RuleMatch(
                rule_name=self.name, severity="MEDIUM", threat_score=55,
                attack_type="Persistence (Possible)",
                description=f"Service installation detected alongside suspicious activity",
                mitre_techniques=["T1543.003"],
                matched_events=service_events,
                hostname=service_events[0].get("hostname", ""),
            )
        return None
