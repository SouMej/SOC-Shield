"""
LangGraph Threat Analysis Workflow — Multi-agent pipeline for threat detection.

Flow: Supervisor → (conditional) → Triage → (conditional) → Correlator → Explainer → Alert
"""
import logging
import time
import uuid
from functools import partial
from typing import Optional

from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq

from config import settings
from ai_engine.state import ThreatAnalysisState
from ai_engine.agents.supervisor import supervisor_node
from ai_engine.agents.triage import triage_node
from ai_engine.agents.correlator import correlator_node
from ai_engine.agents.explainer import explainer_node
from ai_engine.cache import ai_cache

logger = logging.getLogger(__name__)


def _create_llm():
    """Create the Groq LLM instance via langchain-groq."""
    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not set — AI engine will not function")
        return None
    return ChatGroq(
        model=settings.AI_MODEL,
        temperature=settings.AI_TEMPERATURE,
        api_key=settings.GROQ_API_KEY,
    )


def _should_triage(state: ThreatAnalysisState) -> str:
    """Routing: should we proceed to triage?"""
    if state.get("should_alert", False) or state.get("threat_score", 0) > 20:
        return "triage"
    return "end"


def _should_correlate(state: ThreatAnalysisState) -> str:
    """Routing: should we proceed to correlation?"""
    if state.get("threat_score", 0) >= 50:
        return "correlator"
    if state.get("should_alert", False):
        return "explainer"
    return "end"


def build_graph() -> Optional[StateGraph]:
    """Build and compile the LangGraph threat analysis workflow."""
    llm = _create_llm()
    if llm is None:
        return None

    # Create node functions bound to the LLM
    sup = partial(_run_supervisor, llm=llm)
    tri = partial(_run_triage, llm=llm)
    cor = partial(_run_correlator, llm=llm)
    exp = partial(_run_explainer, llm=llm)

    # Build graph
    graph = StateGraph(ThreatAnalysisState)

    graph.add_node("supervisor", sup)
    graph.add_node("triage", tri)
    graph.add_node("correlator", cor)
    graph.add_node("explainer", exp)

    # Entry point
    graph.set_entry_point("supervisor")

    # Conditional edges
    graph.add_conditional_edges("supervisor", _should_triage, {
        "triage": "triage",
        "end": END,
    })
    graph.add_conditional_edges("triage", _should_correlate, {
        "correlator": "correlator",
        "explainer": "explainer",
        "end": END,
    })
    graph.add_edge("correlator", "explainer")
    graph.add_edge("explainer", END)

    compiled = graph.compile()
    logger.info("LangGraph threat analysis workflow compiled successfully")
    return compiled


async def _run_supervisor(state, llm):
    return await supervisor_node(state, llm)

async def _run_triage(state, llm):
    return await triage_node(state, llm)

async def _run_correlator(state, llm):
    return await correlator_node(state, llm)

async def _run_explainer(state, llm):
    return await explainer_node(state, llm)


async def analyze_events(graph, events: list[dict], es_service=None) -> Optional[dict]:
    """Run the full threat analysis pipeline on a batch of events."""
    if graph is None:
        logger.warning("AI graph not available — skipping analysis")
        return None

    start_time = time.time()

    initial_state = {
        "messages": [],
        "raw_events": events,
        "event_count": len(events),
        "triage_result": None,
        "correlation_result": None,
        "final_analysis": None,
        "threat_score": 0,
        "severity": "INFO",
        "attack_type": "Unknown",
        "mitre_techniques": [],
        "should_alert": False,
        "processing_time_ms": 0,
    }

    try:
        # Check cache first
        cached_result = ai_cache.get(events)
        if cached_result:
            return cached_result

        result = await graph.ainvoke(initial_state)
        elapsed = (time.time() - start_time) * 1000

        analysis = result.get("final_analysis") or result.get("triage_result") or {}

        # Detect errors (rate limits, parse failures, etc.)
        has_error = (
            analysis.get("error")
            or "error" in str(analysis.get("explanation", "")).lower()[:30]
            or result.get("attack_type") == "Error"
        )

        if has_error:
            error_msg = analysis.get("error", analysis.get("explanation", "Unknown error"))
            is_rate_limit = "429" in str(error_msg) or "rate_limit" in str(error_msg)
            logger.warning(f"AI analysis had error (rate_limit={is_rate_limit}): {str(error_msg)[:100]}")
            return {"error": str(error_msg), "should_alert": False, "rate_limited": is_rate_limit}

        analysis_record = {
            "analysis_id": str(uuid.uuid4()),
            "severity": result.get("severity", "INFO"),
            "threat_score": result.get("threat_score", 0),
            "attack_type": result.get("attack_type", "Unknown"),
            "confidence": analysis.get("confidence", 0),
            "explanation": analysis.get("explanation", "No analysis available"),
            "title": analysis.get("title", result.get("attack_type", "Security Event")),
            "mitre_techniques": result.get("mitre_techniques", []),
            "recommended_actions": analysis.get("recommended_actions", []),
            "evidence": analysis.get("evidence", []),
            "affected_assets": analysis.get("affected_assets", {}),
            "events_analyzed": len(events),
            "processing_time_ms": round(elapsed, 2),
            "should_alert": result.get("should_alert", False),
        }

        # Store AI analysis in ES — only real, successful analyses
        if es_service and analysis_record["should_alert"]:
            await es_service.index_ai_analysis(analysis_record)
            # Also create an alert
            alert = {
                "alert_id": analysis_record["analysis_id"],
                "severity": analysis_record["severity"],
                "threat_score": analysis_record["threat_score"],
                "attack_type": analysis_record["attack_type"],
                "confidence": analysis_record["confidence"],
                "explanation": analysis_record["explanation"],
                "mitre_techniques": analysis_record["mitre_techniques"],
                "hostname": _extract_primary(events, "hostname"),
                "target_user": _extract_primary(events, "target_user"),
                "source_ip": _extract_primary(events, "source_ip"),
                "related_events": len(events),
                "ai_analysis": True,
                "rule_name": f"AI:{analysis_record['attack_type']}",
            }
            await es_service.index_alert(alert)

        logger.info(f"Analysis complete: score={analysis_record['threat_score']}, "
                     f"type={analysis_record['attack_type']}, time={elapsed:.0f}ms")
                     
        # Cache the successful result
        ai_cache.set(events, analysis_record)
        
        return analysis_record

    except Exception as e:
        logger.error(f"Analysis pipeline error: {e}")
        is_rate_limit = "429" in str(e) or "rate_limit" in str(e)
        return {"error": str(e), "should_alert": False, "rate_limited": is_rate_limit}


def _extract_primary(events: list[dict], field: str) -> str:
    """Extract the most common value for a field from events."""
    counts = {}
    for e in events:
        val = e.get(field)
        if val:
            counts[val] = counts.get(val, 0) + 1
    if counts:
        return max(counts, key=counts.get)
    return "Unknown"
