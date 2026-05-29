"""
Rule Check Tool — Wraps the detection rule engine for use in the AI pipeline.
"""
import logging

logger = logging.getLogger(__name__)


def check_rules_for_events(rule_engine, events: list[dict]) -> list[dict]:
    """Run all detection rules against an event batch and return matches."""
    try:
        matches = rule_engine.evaluate_batch(events)
        return matches
    except Exception as e:
        logger.error(f"Rule check error: {e}")
        return []
