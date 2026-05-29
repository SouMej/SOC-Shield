import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class InMemoryService:
    """
    In-memory replacement for ElasticsearchService.
    Provides identical async methods but stores data in Python lists.
    """
    def __init__(self):
        self.events = []
        self.alerts = []
        self.ai_analyses = []
        logger.info("Initialized InMemoryService for standalone mode.")

    async def connect(self):
        logger.info("InMemoryService connected.")

    async def disconnect(self):
        logger.info("InMemoryService disconnected.")

    async def index_event(self, event: dict) -> str:
        self.events.append(event)
        return "mem-id"

    async def bulk_index_events(self, events: list[dict]) -> int:
        self.events.extend(events)
        return len(events)

    async def search_events(self, query="*", time_from="now-24h", time_to="now", size=50, sort_desc=True):
        return self.events[-size:] if sort_desc else self.events[:size]

    async def get_recent_events(self, size=50, since=None):
        return self.events[-size:]

    async def index_alert(self, alert: dict) -> str:
        if "@timestamp" not in alert:
            alert["@timestamp"] = datetime.utcnow().isoformat() + "Z"
        self.alerts.append(alert)
        return alert.get("alert_id", "mem-alert")

    async def get_alerts(self, severity=None, acknowledged=None, size=100, time_from="now-24h"):
        filtered = self.alerts
        if severity:
            filtered = [a for a in filtered if a.get("severity") == severity]
        if acknowledged is not None:
            filtered = [a for a in filtered if a.get("acknowledged", False) == acknowledged]
        return filtered[-size:]

    async def acknowledge_alert(self, index: str, alert_id: str, user: str) -> bool:
        for a in self.alerts:
            if a.get("alert_id") == alert_id:
                a["acknowledged"] = True
                a["acknowledged_by"] = user
                a["acknowledged_at"] = datetime.utcnow().isoformat() + "Z"
                return True
        return False

    async def index_ai_analysis(self, analysis: dict) -> str:
        if "@timestamp" not in analysis:
            analysis["@timestamp"] = datetime.utcnow().isoformat() + "Z"
        self.ai_analyses.append(analysis)
        return analysis.get("analysis_id", "mem-ai")

    async def get_recent_ai_analyses(self, size=20):
        return self.ai_analyses[-size:]

    async def get_dashboard_stats(self, time_from="now-24h"):
        unack_alerts = sum(1 for a in self.alerts if not a.get("acknowledged", False))
        
        # Aggregate severities
        severities = {}
        top_users = {}
        top_hosts = {}
        for a in self.alerts:
            sev = a.get("severity", "INFO")
            severities[sev] = severities.get(sev, 0) + 1
            
            usr = a.get("target_user", "Unknown")
            if usr != "Unknown":
                top_users[usr] = top_users.get(usr, 0) + 1
                
            hst = a.get("hostname", "Unknown")
            if hst != "Unknown":
                top_hosts[hst] = top_hosts.get(hst, 0) + 1

        sev_list = [{"name": k, "count": v} for k, v in severities.items()]
        usr_list = [{"name": k, "count": v} for k, v in sorted(top_users.items(), key=lambda x: x[1], reverse=True)[:10]]
        hst_list = [{"name": k, "count": v} for k, v in sorted(top_hosts.items(), key=lambda x: x[1], reverse=True)[:10]]

        return {
            "events": {"total": len(self.events)},
            "alerts": {
                "total": len(self.alerts),
                "unacknowledged": unack_alerts,
                "by_severity": sev_list,
                "top_users": usr_list,
                "top_hosts": hst_list
            }
        }

    async def get_severity_distribution(self, time_from="now-24h"):
        severities = {}
        for a in self.alerts:
            sev = a.get("severity", "INFO")
            severities[sev] = severities.get(sev, 0) + 1
        return [{"severity": k, "count": v} for k, v in severities.items()]

    async def get_attack_timeline(self, time_from="now-24h", interval="1h"):
        # For simplicity in memory mode, just group by hour
        buckets = {}
        for a in self.alerts:
            t_str = a.get("@timestamp")
            if t_str:
                try:
                    dt = datetime.fromisoformat(t_str.replace("Z", "+00:00"))
                    hour_key = dt.strftime("%Y-%m-%dT%H:00:00Z")
                    sev = a.get("severity", "INFO")
                    
                    if hour_key not in buckets:
                        buckets[hour_key] = {"total": 0, "severities": {}}
                    
                    buckets[hour_key]["total"] += 1
                    buckets[hour_key]["severities"][sev] = buckets[hour_key]["severities"].get(sev, 0) + 1
                except:
                    pass
                    
        result = []
        for time_key in sorted(buckets.keys()):
            result.append({
                "time": time_key,
                "count": buckets[time_key]["total"],
                "severities": buckets[time_key]["severities"]
            })
        return result[-24:]

    async def get_mitre_heatmap(self, time_from="now-7d"):
        tactics = {}
        for a in self.alerts:
            for tech in a.get("mitre_techniques", []):
                # Basic mock logic for tactics since we don't have the full MITRE DB in memory
                tactic = "Initial Access" if "T1078" in tech else "Privilege Escalation"
                if tactic not in tactics:
                    tactics[tactic] = {}
                tactics[tactic][tech] = tactics[tactic].get(tech, 0) + 1
                
        result = []
        for tac, techs in tactics.items():
            tech_list = [{"id": k, "name": k, "count": v} for k, v in techs.items()]
            result.append({
                "tactic": tac,
                "techniques": tech_list
            })
        return result

    async def health_check(self):
        return {
            "status": "green",
            "cluster_name": "in-memory-cluster",
            "number_of_nodes": 1,
            "active_primary_shards": 0,
            "active_shards": 0
        }

# Global singleton instance for standalone mode
es_service = InMemoryService()
