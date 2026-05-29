"""
Lateral Movement Detection Rule
"""
from collections import defaultdict


class LateralMovementRule:
    """Detects lateral movement: same user, network logons across multiple hosts."""
    name = "Lateral Movement Detection"

    def evaluate(self, events):
        network_logons = [
            e for e in events
            if e.get("event_id") == 4624 and e.get("logon_type") == 3
        ]
        if len(network_logons) < 3:
            return None

        by_user = defaultdict(set)
        by_user_events = defaultdict(list)
        for e in network_logons:
            user = e.get("target_user", "unknown")
            host = e.get("hostname", "unknown")
            if user.lower() not in ("anonymous logon", "system", "") and not user.endswith("$"):
                by_user[user].add(host)
                by_user_events[user].append(e)

        from detection_rules.rule_engine import RuleMatch
        matches = []
        for user, hosts in by_user.items():
            if len(hosts) >= 3:
                evts = by_user_events[user]
                score = min(95, 55 + len(hosts) * 8)
                matches.append(RuleMatch(
                    rule_name=self.name, severity="HIGH", threat_score=score,
                    attack_type="Lateral Movement",
                    description=f"User '{user}' performed network logons to {len(hosts)} hosts: {', '.join(list(hosts)[:5])}",
                    mitre_techniques=["T1021", "T1021.002"],
                    matched_events=evts, hostname=list(hosts)[0],
                    user=user, source_ip=evts[0].get("source_ip", ""),
                ))
        return matches if matches else None
