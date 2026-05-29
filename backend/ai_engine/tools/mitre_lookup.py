"""
MITRE ATT&CK Lookup Tool — Maps attack indicators to MITRE techniques.
"""

# MITRE ATT&CK mapping for common AD attacks
MITRE_TECHNIQUES = {
    "T1110": {"name": "Brute Force", "tactic": "Credential Access",
              "description": "Adversaries may use brute force techniques to gain access to accounts."},
    "T1110.001": {"name": "Password Guessing", "tactic": "Credential Access",
                  "description": "Adversaries may guess passwords to attempt access to accounts."},
    "T1110.003": {"name": "Password Spraying", "tactic": "Credential Access",
                  "description": "Adversaries may use a single or small list of commonly used passwords against many accounts."},
    "T1003": {"name": "OS Credential Dumping", "tactic": "Credential Access",
              "description": "Adversaries may attempt to dump credentials from the OS."},
    "T1003.006": {"name": "DCSync", "tactic": "Credential Access",
                  "description": "Adversaries may attempt to replicate AD data via DCSync."},
    "T1558.003": {"name": "Kerberoasting", "tactic": "Credential Access",
                  "description": "Adversaries may abuse Kerberos TGS to obtain service account credentials."},
    "T1558.004": {"name": "AS-REP Roasting", "tactic": "Credential Access",
                  "description": "Adversaries may exploit Kerberos pre-auth disabled accounts."},
    "T1550.002": {"name": "Pass the Hash", "tactic": "Lateral Movement",
                  "description": "Adversaries may use stolen password hashes to move laterally."},
    "T1021": {"name": "Remote Services", "tactic": "Lateral Movement",
              "description": "Adversaries may use remote services to move laterally."},
    "T1021.002": {"name": "SMB/Windows Admin Shares", "tactic": "Lateral Movement",
                  "description": "Adversaries may use SMB to interact with remote shares."},
    "T1078": {"name": "Valid Accounts", "tactic": "Privilege Escalation",
              "description": "Adversaries may use valid accounts for privilege escalation."},
    "T1078.002": {"name": "Domain Accounts", "tactic": "Privilege Escalation",
                  "description": "Adversaries may use domain accounts for privilege escalation."},
    "T1059.001": {"name": "PowerShell", "tactic": "Execution",
                  "description": "Adversaries may abuse PowerShell for execution."},
    "T1543.003": {"name": "Windows Service", "tactic": "Persistence",
                  "description": "Adversaries may create or modify Windows services for persistence."},
    "T1098": {"name": "Account Manipulation", "tactic": "Persistence",
              "description": "Adversaries may manipulate accounts to maintain access."},
    "T1136": {"name": "Create Account", "tactic": "Persistence",
              "description": "Adversaries may create accounts to maintain access."},
    "T1053": {"name": "Scheduled Task/Job", "tactic": "Persistence",
              "description": "Adversaries may abuse task scheduling for persistence."},
    "T1547.001": {"name": "Registry Run Keys", "tactic": "Persistence",
                  "description": "Adversaries may use registry run keys for persistence."},
}

# MITRE Tactics in order
MITRE_TACTICS = [
    "Reconnaissance", "Resource Development", "Initial Access", "Execution",
    "Persistence", "Privilege Escalation", "Defense Evasion", "Credential Access",
    "Discovery", "Lateral Movement", "Collection", "Command and Control",
    "Exfiltration", "Impact"
]


def lookup_technique(technique_id: str) -> dict:
    """Look up a MITRE ATT&CK technique by ID."""
    return MITRE_TECHNIQUES.get(technique_id, {
        "name": "Unknown Technique",
        "tactic": "Unknown",
        "description": f"Technique {technique_id} not in local database."
    })


def get_techniques_by_tactic(tactic: str) -> list[dict]:
    """Get all techniques for a given tactic."""
    return [
        {"id": tid, **info}
        for tid, info in MITRE_TECHNIQUES.items()
        if info["tactic"] == tactic
    ]


def get_all_techniques() -> list[dict]:
    """Get all known techniques."""
    return [{"id": tid, **info} for tid, info in MITRE_TECHNIQUES.items()]


def get_heatmap_data() -> list[dict]:
    """Get technique data organized by tactic for heatmap visualization."""
    result = []
    for tactic in MITRE_TACTICS:
        techniques = get_techniques_by_tactic(tactic)
        result.append({"tactic": tactic, "techniques": techniques})
    return result
