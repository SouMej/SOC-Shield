"""
PowerShell Abuse Detection Rule
"""
import re


class PowerShellAbuseRule:
    """Detects suspicious PowerShell execution patterns."""
    name = "PowerShell Abuse Detection"

    SUSPICIOUS_PATTERNS = [
        r"-enc\b", r"-EncodedCommand", r"FromBase64String",
        r"IEX\b", r"Invoke-Expression", r"Invoke-WebRequest",
        r"DownloadString", r"Net\.WebClient", r"downloadfile",
        r"-nop\b.*-w\s+hidden", r"Invoke-Mimikatz", r"Invoke-Shellcode",
        r"Get-GPPPassword", r"Invoke-Kerberoast", r"Invoke-BloodHound",
    ]

    def evaluate(self, events):
        proc_events = [
            e for e in events
            if e.get("event_id") in (4688, 1)
            and "powershell" in (e.get("process_name") or "").lower()
        ]
        if not proc_events:
            return None

        from detection_rules.rule_engine import RuleMatch
        suspicious = []
        for e in proc_events:
            cmd = e.get("command_line", "")
            if any(re.search(p, cmd, re.IGNORECASE) for p in self.SUSPICIOUS_PATTERNS):
                suspicious.append(e)

        if suspicious:
            score = min(95, 60 + len(suspicious) * 10)
            sev = "CRITICAL" if score >= 85 else "HIGH"
            cmds = [e.get("command_line", "?")[:100] for e in suspicious[:3]]
            return RuleMatch(
                rule_name=self.name, severity=sev, threat_score=score,
                attack_type="PowerShell Abuse",
                description=f"{len(suspicious)} suspicious PowerShell executions detected. Samples: {'; '.join(cmds)}",
                mitre_techniques=["T1059.001"],
                matched_events=suspicious,
                hostname=suspicious[0].get("hostname", ""),
                user=suspicious[0].get("subject_user", ""),
            )
        return None
