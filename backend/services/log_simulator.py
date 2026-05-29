import asyncio
import logging
import csv
import os
import random
import uuid
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# Try importing Kafka, but make it optional
try:
    from aiokafka import AIOKafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False


class AttackInjector:
    """Generates synthetic, dynamic attack events that match our detection rules."""
    
    @staticmethod
    def generate_brute_force(timestamp):
        target = f"user_{random.randint(100, 999)}"
        ip = f"10.0.{random.randint(1,255)}.{random.randint(1,255)}"
        events = []
        for _ in range(6):
            events.append({
                "@timestamp": timestamp,
                "event_id": 4625,
                "hostname": "DC01",
                "source_ip": ip,
                "target_user": target,
                "message": "An account failed to log on.",
                "logon_type": "3",
                "status": "0xC000006D",
                "provider": "Microsoft-Windows-Security-Auditing",
                "severity": "INFO",
            })
        return events

    @staticmethod
    def generate_kerberoasting(timestamp):
        ip = f"10.0.50.{random.randint(10,50)}"
        targets = ["svc_sql", "svc_web", "svc_backup"]
        events = []
        for target in targets:
            events.append({
                "@timestamp": timestamp,
                "event_id": 4769,
                "hostname": "DC01",
                "source_ip": ip,
                "target_user": target,
                "message": "A Kerberos service ticket was requested. Encryption Type: 0x17",
                "logon_type": "",
                "status": "",
                "provider": "Microsoft-Windows-Security-Auditing",
                "severity": "INFO",
            })
        return events

    @staticmethod
    def generate_priv_escalation(timestamp):
        user = f"contractor_{random.randint(10,99)}"
        events = []
        for _ in range(2):
            events.append({
                "@timestamp": timestamp,
                "event_id": 4672,
                "hostname": f"WS-{random.randint(100,200)}",
                "source_ip": "127.0.0.1",
                "subject_user": user,
                "target_user": user,
                "message": "Special privileges assigned to new logon.",
                "logon_type": "2",
                "status": "",
                "provider": "Microsoft-Windows-Security-Auditing",
                "severity": "INFO",
            })
        return events

    @staticmethod
    def generate_persistence(timestamp):
        events = [{
            "@timestamp": timestamp,
            "event_id": 4697,
            "hostname": f"SRV-{random.randint(10, 50)}",
            "source_ip": "127.0.0.1",
            "target_user": "SYSTEM",
            "message": "A service was installed in the system. Service File Name: C:\\Windows\\Temp\\malicious.exe",
            "logon_type": "",
            "status": "",
            "provider": "Microsoft-Windows-Security-Auditing",
            "severity": "INFO",
        }]
        return events

    @staticmethod
    def generate_lateral_movement(timestamp):
        events = [{
            "@timestamp": timestamp,
            "event_id": 5140,
            "hostname": "FS01",
            "source_ip": f"10.0.100.{random.randint(10,50)}",
            "target_user": "admin_jdoe",
            "message": "A network share object was accessed. Share Name: \\\\*\\C$",
            "logon_type": "3",
            "status": "",
            "provider": "Microsoft-Windows-Security-Auditing",
            "severity": "INFO",
        }]
        return events

    @staticmethod
    def generate_powershell_abuse(timestamp):
        events = [{
            "@timestamp": timestamp,
            "event_id": 4104,
            "hostname": f"WS-{random.randint(10, 50)}",
            "source_ip": "127.0.0.1",
            "target_user": "user_ps",
            "message": "Creating Scriptblock text: powershell.exe -enc JABzAD0ATgBlAHcALQBPAGIAagBlAGMAdAAgAEkATwAuAE0AZQBtAG8AcgB5AFMAdAByAGUAYQBtACgAWwBDAG8AbgB2AGUAcgB0AF0AOgA6AEYAcgBvAG0AQgBhAHMAZQA2ADQAUwB0AHIAaQBuAGcAKAAiAEgA...",
            "logon_type": "",
            "status": "",
            "provider": "Microsoft-Windows-PowerShell",
            "severity": "INFO",
        }]
        return events

    @classmethod
    def get_random_attack(cls):
        attacks = [
            cls.generate_brute_force,
            cls.generate_kerberoasting,
            cls.generate_priv_escalation,
            cls.generate_persistence,
            cls.generate_lateral_movement,
            cls.generate_powershell_abuse
        ]
        return random.choice(attacks)


class LogSimulator:
    """Reads events from CSV and simulates live indexing.
    Sends to Kafka if available, otherwise indexes directly to Elasticsearch."""

    def __init__(self, es_service):
        self.es = es_service
        self.running = False
        self.events_generated = 0
        self.csv_path = "../Untitled-Discover-session.csv"
        self.raw_events = []
        self.producer = None
        self._use_kafka = False

    def _load_csv(self):
        if not os.path.exists(self.csv_path):
            logger.error(f"Cannot find CSV at {self.csv_path}")
            return

        with open(self.csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get("event.code"):
                    continue
                try:
                    event_id = int(row["event.code"])
                except ValueError:
                    continue

                event = {
                    "@timestamp": row.get("@timestamp") or datetime.utcnow().isoformat() + "Z",
                    "event_id": event_id,
                    "hostname": row.get("host.hostname") or row.get("winlog.computer_name") or "unknown-host",
                    "source_ip": row.get("source.ip") or row.get("host.ip", "").split(",")[0].strip() or "127.0.0.1",
                    "target_user": row.get("user.name") or row.get("winlog.event_data.TargetUserName") or "SYSTEM",
                    "message": row.get("message", ""),
                    "logon_type": row.get("winlog.event_data.LogonType"),
                    "status": row.get("winlog.event_data.Status"),
                    "provider": row.get("event.provider", "Microsoft-Windows-Security-Auditing"),
                    "severity": "INFO",
                }
                self.raw_events.append(event)
        logger.info(f"Simulator loaded {len(self.raw_events)} events from CSV.")

    async def start(self, interval: float = 3.0):
        self._load_csv()
        if not self.raw_events:
            logger.error("No events to simulate. Stopping.")
            return

        self.running = True
        logger.info(f"Log simulator started streaming CSV (interval: {interval}s)")
        
        # Try to connect to Kafka
        if KAFKA_AVAILABLE:
            try:
                self.producer = AIOKafkaProducer(bootstrap_servers='soc-kafka:9092')
                await self.producer.start()
                self._use_kafka = True
                logger.info("✓ Simulator connected to Kafka — streaming via broker")
            except Exception as e:
                logger.warning(f"✗ Kafka not available ({e}) — indexing directly to Elasticsearch")
                self.producer = None
                self._use_kafka = False
        else:
            logger.info("Kafka library not installed — indexing directly to Elasticsearch")

        idx = 0
        batch_size = 5
        loop_counter = 0
        
        while self.running:
            try:
                loop_counter += 1
                batch = []
                now = datetime.utcnow().isoformat() + "Z"

                # 1. Normal Baseline Traffic (from CSV)
                csv_batch = self.raw_events[idx:idx+batch_size]
                idx += batch_size
                if idx >= len(self.raw_events):
                    idx = 0
                    
                for e in csv_batch:
                    # Make a shallow copy so we don't mutate the raw list
                    new_e = e.copy()
                    new_e["@timestamp"] = now
                    batch.append(new_e)

                # 2. Inject Synthetic Attack randomly (e.g. 1 in 5 chance per interval = every ~15 secs)
                if random.random() < 0.20:
                    attack_func = AttackInjector.get_random_attack()
                    attack_events = attack_func(now)
                    batch.extend(attack_events)
                    logger.info(f"💉 Injected synthetic attack sequence: {attack_func.__name__} ({len(attack_events)} events)")

                if batch:
                    if self._use_kafka:
                        for event in batch:
                            await self.producer.send_and_wait('soc-logs', json.dumps(event).encode('utf-8'))
                        self.events_generated += len(batch)
                        logger.info(f"Simulator: sent {len(batch)} events to Kafka (total: {self.events_generated})")
                    else:
                        await self.es.bulk_index_events(batch)
                        self.events_generated += len(batch)
                        logger.info(f"Simulator: indexed {len(batch)} events to ES (total: {self.events_generated})")
                    
            except Exception as e:
                logger.error(f"Simulator error: {e}")
                
            await asyncio.sleep(interval)

    async def stop(self):
        self.running = False
        if self.producer:
            try:
                await self.producer.stop()
            except Exception:
                pass
        logger.info(f"Log simulator stopped. Total events: {self.events_generated}")
