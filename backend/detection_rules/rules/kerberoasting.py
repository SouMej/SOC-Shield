"""
Kerberoasting Detection Rule
"""
from collections import defaultdict


class KerberoastingRule:
    """Detects Kerberoasting: multiple TGS requests for service accounts."""
    name = "Kerberoasting Detection"

    SERVICE_ACCOUNTS = {"svc_sql", "svc_web", "svc_backup", "svc_exchange",
                        "svc_iis", "svc_ftp", "svc_mail"}

    def evaluate(self, events):
        tgs_requests = [e for e in events if e.get("event_id") == 4769]
        if len(tgs_requests) < 3:
            return None

        by_source = defaultdict(list)
        for e in tgs_requests:
            ip = e.get("source_ip", "unknown")
            by_source[ip].append(e)

        from detection_rules.rule_engine import RuleMatch
        for ip, evts in by_source.items():
            svc_targets = [
                e for e in evts
                if (e.get("target_user") or "").lower() in self.SERVICE_ACCOUNTS
            ]
            if len(svc_targets) >= 3:
                users = list(set(e.get("target_user", "?") for e in svc_targets))
                return RuleMatch(
                    rule_name=self.name, severity="HIGH", threat_score=85,
                    attack_type="Kerberoasting",
                    description=f"Potential Kerberoasting from {ip}: TGS requests for service accounts: {', '.join(users)}",
                    mitre_techniques=["T1558.003"],
                    matched_events=svc_targets,
                    hostname=svc_targets[0].get("hostname", ""),
                    source_ip=ip,
                )
        return None
