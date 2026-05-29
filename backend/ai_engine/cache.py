"""
Semantic Cache for AI Analysis.
Stores recent analyses to avoid hitting the LLM for identical repeated attacks.
"""
import time
import hashlib
import logging

logger = logging.getLogger(__name__)

class AICache:
    def __init__(self, ttl_seconds: int = 3600):
        self.cache = {}
        self.ttl = ttl_seconds

    def _hash_events(self, events: list[dict]) -> str:
        """Create a signature for a batch of events, focusing on key fields."""
        # We extract just the core properties that define an attack to normalize it
        signature_parts = []
        for e in sorted(events, key=lambda x: str(x.get('event_id'))):
            sig = f"{e.get('event_id')}_{e.get('hostname')}_{e.get('source_ip')}_{e.get('target_user')}"
            if e.get("command_line"):
                sig += f"_{e.get('command_line')}"
            signature_parts.append(sig)
            
        full_sig = "|".join(signature_parts)
        return hashlib.md5(full_sig.encode()).hexdigest()

    def get(self, events: list[dict]):
        if not events:
            return None
            
        key = self._hash_events(events)
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['time'] < self.ttl:
                logger.info("AI Cache Hit! Skipping LLM call.")
                return entry['result']
            else:
                del self.cache[key]
        return None

    def set(self, events: list[dict], result: dict):
        if not events or not result:
            return
            
        key = self._hash_events(events)
        # Deep copy the result to avoid mutations, but simple dict is fine
        self.cache[key] = {
            'time': time.time(),
            'result': result
        }

ai_cache = AICache(ttl_seconds=3600)  # 1 hour TTL
