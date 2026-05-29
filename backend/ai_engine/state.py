"""
AI Engine State — Typed state schema for the LangGraph threat analysis workflow.
"""
from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages


class ThreatAnalysisState(TypedDict):
    """State that flows through the LangGraph threat analysis pipeline."""
    # LLM conversation messages
    messages: Annotated[list, add_messages]
    # Raw batch of security events from Elasticsearch
    raw_events: list[dict]
    # Number of events in the batch
    event_count: int
    # Triage agent output
    triage_result: Optional[dict]
    # Correlator agent output
    correlation_result: Optional[dict]
    # Final analysis report
    final_analysis: Optional[dict]
    # Computed threat score (0-100)
    threat_score: int
    # Severity classification
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    # Detected attack type
    attack_type: str
    # MITRE ATT&CK technique IDs
    mitre_techniques: list[str]
    # Whether to generate an alert
    should_alert: bool
    # Processing metadata
    processing_time_ms: float
