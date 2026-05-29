"""
Brute Force & Password Spraying Detection Rules
"""
from collections import defaultdict


class BruteForceRule:
    """Detects brute force attacks: >5 failed logins from same source in batch."""
    name = "Brute Force Detection"

    def evaluate(self, events):
        failed = [e for e in events if e.get("event_id") == 4625]
        if len(failed) < 5:
            return None

        by_source = defaultdict(list)
        for e in failed:
            key = e.get("source_ip", "unknown")
            by_source[key].append(e)

        from detection_rules.rule_engine import RuleMatch
        matches = []
        for ip, evts in by_source.items():
            if len(evts) >= 5:
                targets = list(set(e.get("target_user", "?") for e in evts))
                host = evts[0].get("hostname", "Unknown")
                score = min(95, 50 + len(evts) * 3)
                sev = "CRITICAL" if len(evts) >= 15 else "HIGH" if len(evts) >= 10 else "MEDIUM"
                matches.append(RuleMatch(
                    rule_name=self.name, severity=sev, threat_score=score,
                    attack_type="Brute Force",
                    description=f"{len(evts)} failed login attempts from {ip} targeting {', '.join(targets[:5])} on {host}",
                    mitre_techniques=["T1110.001"],
                    matched_events=evts, hostname=host,
                    user=targets[0] if targets else "", source_ip=ip,
                ))
        return matches if matches else None


class PasswordSprayRule:
    """Detects password spraying: same source, many different target users."""
    name = "Password Spray Detection"

    def evaluate(self, events):
        failed = [e for e in events if e.get("event_id") == 4625]
        if len(failed) < 4:
            return None

        by_source = defaultdict(set)
        by_source_events = defaultdict(list)
        for e in failed:
            ip = e.get("source_ip", "unknown")
            user = e.get("target_user", "unknown")
            by_source[ip].add(user)
            by_source_events[ip].append(e)

        from detection_rules.rule_engine import RuleMatch
        matches = []
        for ip, users in by_source.items():
            if len(users) >= 4:
                evts = by_source_events[ip]
                score = min(98, 60 + len(users) * 4)
                matches.append(RuleMatch(
                    rule_name=self.name, severity="HIGH", threat_score=score,
                    attack_type="Password Spraying",
                    description=f"Password spray from {ip}: {len(users)} unique users targeted ({', '.join(list(users)[:5])})",
                    mitre_techniques=["T1110.003"],
                    matched_events=evts, hostname=evts[0].get("hostname", ""),
                    user=list(users)[0], source_ip=ip,
                ))
        return matches if matches else None
