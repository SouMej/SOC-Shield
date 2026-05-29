"""
Privilege Escalation Detection Rule
"""


class PrivilegeEscalationRule:
    """Detects suspicious privilege assignment to non-admin accounts."""
    name = "Privilege Escalation Detection"

    KNOWN_ADMINS = {"administrator", "svc_backup", "svc_sql", "krbtgt"}

    def evaluate(self, events):
        priv_events = [e for e in events if e.get("event_id") == 4672]
        if not priv_events:
            return None

        from detection_rules.rule_engine import RuleMatch
        suspicious = []
        for e in priv_events:
            user = (e.get("subject_user") or "").lower()
            if user and user not in self.KNOWN_ADMINS and not user.endswith("$"):
                suspicious.append(e)

        if len(suspicious) >= 2:
            users = list(set(e.get("subject_user", "?") for e in suspicious))
            return RuleMatch(
                rule_name=self.name, severity="HIGH", threat_score=75,
                attack_type="Privilege Escalation",
                description=f"Suspicious privilege assignment to non-admin users: {', '.join(users[:5])}",
                mitre_techniques=["T1078", "T1078.002"],
                matched_events=suspicious,
                hostname=suspicious[0].get("hostname", ""),
                user=users[0],
            )
        return None
