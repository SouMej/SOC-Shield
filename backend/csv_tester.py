import asyncio
import csv
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load backend environment variables
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from config import settings
from detection_rules.rule_engine import RuleEngine
from ai_engine.graph import build_graph, analyze_events

async def main():
    print("==================================================")
    print(" SOCPlatform: CSV Ingestion & AI Testing Script")
    print("==================================================")
    print(f"[*] AI Model: {settings.AI_MODEL}")
    print(f"[*] API Key config: {'Configured' if settings.GROQ_API_KEY else 'MISSING'}")
    
    if not settings.GROQ_API_KEY:
        print("[!] Cannot test AI agent: GROQ_API_KEY is missing in .env")
        return

    csv_path = "../Untitled-Discover-session.csv"
    if not os.path.exists(csv_path):
        print(f"[!] Cannot find CSV file at: {csv_path}")
        return

    print(f"[*] Loading dataset: {csv_path}")
    events = []
    
    # Read CSV and map fields to expected Event format
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip empty or malformed rows
            if not row.get("event.code"):
                continue
                
            try:
                event_id = int(row["event.code"])
            except ValueError:
                continue

            # Construct our standardized event dictionary
            event = {
                "@timestamp": row.get("@timestamp") or datetime.utcnow().isoformat() + "Z",
                "event_id": event_id,
                "hostname": row.get("host.hostname") or row.get("winlog.computer_name") or "unknown-host",
                "source_ip": row.get("source.ip") or row.get("host.ip", "").split(",")[0].strip() or "127.0.0.1",
                "user": row.get("user.name") or row.get("winlog.event_data.TargetUserName") or "SYSTEM",
                "message": row.get("message", ""),
                "event_data": {
                    "LogonType": row.get("winlog.event_data.LogonType"),
                    "TargetUserName": row.get("winlog.event_data.TargetUserName"),
                    "Status": row.get("winlog.event_data.Status"),
                    "ServiceName": row.get("winlog.event_data.ServiceName"),
                    "CommandLine": row.get("winlog.event_data.CommandLine") or row.get("process.command_line"),
                }
            }
            events.append(event)
            
            # Read first 50 valid events for a quick test batch
            if len(events) >= 50:
                break

    print(f"[*] Successfully parsed {len(events)} events from CSV.")
    if len(events) == 0:
        print("[!] No valid events found. Exiting.")
        return

    print("\n[*] Initializing Rule Engine...")
    rule_engine = RuleEngine()
    
    print("[*] Running batch through Detection Rules...")
    rule_matches = rule_engine.evaluate_batch(events)
    
    print(f"[+] Rule Engine generated {len(rule_matches)} alerts.")
    for match in rule_matches:
        print(f"    - {match['severity']} Alert: {match['rule_name']} ({match['mitre_technique']})")

    # If we didn't get any rule matches, let's artificially trigger the AI by pretending
    # all events are potentially suspicious to test the AI pipeline on real logs
    if not rule_matches:
        print("\n[*] No explicit rule matches. Forcing AI pipeline test on raw events...")

    print("\n==================================================")
    print(" STARTING AI AGENT THREAT ANALYSIS (GROQ)")
    print("==================================================")
    
    try:
        # Initialize LangGraph pipeline
        graph = build_graph()
        
        print("[*] Dispatching events to LangGraph AI Agent Pipeline...")
        # Run graph
        result_state = await analyze_events(graph, events)
        
        print("\n==================================================")
        print(" AI THREAT ANALYSIS RESULTS")
        print("==================================================")
        print(f"[*] Attack Type       : {result_state.get('attack_type')}")
        print(f"[*] Severity          : {result_state.get('severity')}")
        print(f"[*] Threat Score      : {result_state.get('threat_score')}/100")
        print(f"[*] Confidence        : {result_state.get('confidence')}%")
        
        if result_state.get('mitre_techniques'):
            print(f"[*] MITRE Techniques  : {', '.join(result_state.get('mitre_techniques'))}")
            
        if result_state.get('recommended_actions'):
            print("[*] Recommended Actions:")
            for action in result_state.get('recommended_actions', []):
                print(f"    - {action}")
                
        if result_state.get('explanation'):
            print("\n[*] Explanation:")
            print(result_state.get('explanation'))
        
        # Save output
        output_file = "test_results.json"
        with open(output_file, "w") as f:
            json.dump(result_state, f, indent=2)
            
        print(f"\n[+] Full AI analysis results saved to backend/{output_file}")
        
    except Exception as e:
        print(f"\n[!] AI Agent execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
