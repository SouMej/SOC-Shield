"""
Explainer Agent — Produces final human-readable threat analysis reports.
"""
import json
import logging
from langchain_core.messages import HumanMessage, SystemMessage
from ai_engine.prompts import EXPLAINER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


async def explainer_node(state: dict, llm) -> dict:
    """Explainer agent: generates final threat report for SOC analysts."""
    triage = state.get("triage_result", {})
    correlation = state.get("correlation_result", {})
    events = state["raw_events"]

    context = (
        f"Generate a final threat analysis report.\n\n"
        f"Triage Analysis:\n{json.dumps(triage, default=str)}\n\n"
        f"Correlation Analysis:\n{json.dumps(correlation, default=str)}\n\n"
        f"Current Threat Score: {state.get('threat_score', 0)}\n"
        f"Current Severity: {state.get('severity', 'UNKNOWN')}\n"
        f"Events Analyzed: {len(events)}\n"
        f"Detected Attack Type: {state.get('attack_type', 'Unknown')}\n"
    )

    messages = [
        SystemMessage(content=EXPLAINER_SYSTEM_PROMPT),
        HumanMessage(content=context),
    ]

    try:
        response = await llm.ainvoke(messages)
        result = _parse_json(response.content)

        logger.info(f"Explainer: title='{result.get('title')}', score={result.get('threat_score')}")

        return {
            "messages": state.get("messages", []) + messages + [response],
            "final_analysis": result,
            "threat_score": result.get("threat_score", state.get("threat_score", 0)),
            "severity": result.get("severity", state.get("severity", "MEDIUM")),
            "attack_type": result.get("attack_type", state.get("attack_type", "Unknown")),
            "mitre_techniques": [
                t["id"] if isinstance(t, dict) else t
                for t in result.get("mitre_techniques", state.get("mitre_techniques", []))
            ],
            "should_alert": True,
        }
    except Exception as e:
        logger.error(f"Explainer agent error: {e}")
        return {
            "final_analysis": {
                "severity": state.get("severity", "MEDIUM"),
                "threat_score": state.get("threat_score", 50),
                "attack_type": state.get("attack_type", "Unknown"),
                "title": "Analysis Error",
                "explanation": f"AI analysis encountered an error: {str(e)}",
                "error": str(e),
            }
        }


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
    return {"error": "Parse failed", "raw": text[:500]}
