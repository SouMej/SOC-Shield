import sys
import os
import asyncio
from pathlib import Path

# Ajouter le backend au path pour importer les modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.rag_service import rag_service

MITRE_MOCK_DATA = [
    {
        "text": "T1059.001 - PowerShell: Adversaries may abuse PowerShell commands and scripts for execution. PowerShell is a powerful interactive command-line interface and scripting environment included in the Windows operating system.",
        "metadata": {"technique_id": "T1059.001", "name": "PowerShell", "tactic": "Execution"}
    },
    {
        "text": "T1078 - Valid Accounts: Adversaries may obtain and abuse credentials of existing accounts as a means of gaining Initial Access, Persistence, Privilege Escalation, or Defense Evasion.",
        "metadata": {"technique_id": "T1078", "name": "Valid Accounts", "tactic": "Initial Access"}
    },
    {
        "text": "T1110 - Brute Force: Adversaries may use brute force techniques to gain access to accounts when passwords are unknown or when password hashes are obtained.",
        "metadata": {"technique_id": "T1110", "name": "Brute Force", "tactic": "Credential Access"}
    },
    {
        "text": "T1047 - Windows Management Instrumentation (WMI): Adversaries may abuse WMI to execute malicious commands and payloads.",
        "metadata": {"technique_id": "T1047", "name": "Windows Management Instrumentation", "tactic": "Execution"}
    },
    {
        "text": "T1098 - Account Manipulation: Adversaries may manipulate accounts to maintain access to victim systems. Account manipulation may consist of any action that preserves adversary access to a compromised account.",
        "metadata": {"technique_id": "T1098", "name": "Account Manipulation", "tactic": "Persistence"}
    }
]

def ingest():
    print("Ingestion de la base MITRE ATT&CK dans Elasticsearch (RAG)...")
    texts = [item["text"] for item in MITRE_MOCK_DATA]
    metadatas = [item["metadata"] for item in MITRE_MOCK_DATA]
    
    rag_service.add_documents(texts, metadatas)
    print("Ingestion terminée avec succès !")

if __name__ == "__main__":
    ingest()
