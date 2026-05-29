"""
SOC Copilot Chatbot — WebSocket endpoint with RAG-enriched, context-aware SOC assistant.
"""
import logging
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from config import settings
from services.elasticsearch_service import es_service

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory chat history per client
chat_histories = {}

SOC_COPILOT_SYSTEM_PROMPT = """Tu es **SOC Copilot**, un assistant expert en cybersécurité embarqué dans une plateforme SOC (Security Operations Center) de niveau entreprise.

Tu assistes les analystes SOC dans leur travail quotidien. Tu es spécialisé dans :
- L'analyse et l'investigation des alertes de sécurité Active Directory / Windows
- La classification des menaces selon le framework MITRE ATT&CK
- Les recommandations de remédiation et réponse aux incidents
- L'explication des logs Windows (Event IDs 4625, 4672, 4769, 4688, 4720, 5140, 7045, etc.)
- Les techniques d'attaque : Brute Force, Kerberoasting, Pass-the-Hash, Lateral Movement, Privilege Escalation, Persistence, PowerShell abuse
- Les commandes de défense Windows : PowerShell, netsh, wevtutil, Get-WinEvent, etc.

**Règles importantes :**
1. Réponds TOUJOURS en français sauf si l'utilisateur parle anglais.
2. Sois concis, précis et actionnable. Pas de bavardage inutile.
3. Si on te donne un contexte d'alertes récentes, utilise-le pour tes analyses.
4. Fournis des commandes concrètes quand c'est pertinent (PowerShell, KQL, etc.)
5. Cite les techniques MITRE ATT&CK avec leurs IDs (ex: T1110.001 — Brute Force).
6. Structure tes réponses avec des titres et des listes pour la lisibilité.
7. Si tu ne sais pas, dis-le honnêtement au lieu d'inventer.

**Contexte de la plateforme :**
- Backend : FastAPI + Elasticsearch + Kafka
- Moteur de détection : Rule Engine + LangGraph AI Agents
- Sources de logs : Sysmon, Winlogbeat, Active Directory, Windows Security Events
"""


def get_llm():
    if not settings.GROQ_API_KEY:
        return None
    return ChatGroq(
        model=settings.AI_MODEL,
        temperature=0.3,
        api_key=settings.GROQ_API_KEY,
        max_tokens=1024,
    )


async def _get_recent_alerts_context() -> str:
    """Fetch recent alerts from Elasticsearch to give the chatbot live context."""
    try:
        alerts = await es_service.get_recent_alerts(size=10)
        if not alerts:
            return "\n[Aucune alerte récente détectée dans le système.]"

        lines = [f"\n--- {len(alerts)} ALERTES RÉCENTES DANS LE SYSTÈME ---"]
        for i, a in enumerate(alerts[:10]):
            lines.append(
                f"{i+1}. [{a.get('severity', '?')}] {a.get('attack_type', a.get('rule_name', '?'))} "
                f"| Score: {a.get('threat_score', '?')} "
                f"| Host: {a.get('hostname', '?')} "
                f"| User: {a.get('target_user', '?')} "
                f"| IP: {a.get('source_ip', '?')} "
                f"| MITRE: {', '.join(a.get('mitre_techniques', []))}"
            )
        return "\n".join(lines)
    except Exception as e:
        logger.warning(f"Failed to fetch alerts for chatbot context: {e}")
        return "\n[Impossible de récupérer les alertes récentes.]"


@router.websocket("/ws/chat/{client_id}")
async def websocket_chat_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()

    # Build system prompt with live alert context
    alerts_context = await _get_recent_alerts_context()
    system_prompt = SOC_COPILOT_SYSTEM_PROMPT + alerts_context

    if client_id not in chat_histories:
        chat_histories[client_id] = [
            SystemMessage(content=system_prompt)
        ]

    llm = get_llm()
    if not llm:
        await websocket.send_json({
            "message": "⚠️ SOC Copilot n'est pas disponible — la clé API Groq n'est pas configurée. "
                       "Vérifiez le fichier .env du backend."
        })
        await websocket.close()
        return

    logger.info(f"Client {client_id} connecté au chatbot SOC.")

    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Chatbot ({client_id}): {data[:100]}")

            chat_histories[client_id].append(HumanMessage(content=data))

            # Keep conversation manageable — trim to last 20 messages + system
            if len(chat_histories[client_id]) > 21:
                chat_histories[client_id] = [
                    chat_histories[client_id][0]  # keep system prompt
                ] + chat_histories[client_id][-20:]

            try:
                response = await llm.ainvoke(chat_histories[client_id])
                chat_histories[client_id].append(response)
                await websocket.send_json({"message": response.content})
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "rate_limit" in error_str:
                    await websocket.send_json({
                        "message": "⏸ **Rate limit atteint** — L'API Groq a dépassé son quota journalier. "
                                   "Le chatbot sera de nouveau disponible dans quelques minutes. "
                                   "En attendant, vous pouvez consulter les alertes directement dans le dashboard."
                    })
                else:
                    logger.error(f"Chatbot LLM error: {e}")
                    await websocket.send_json({
                        "message": f"❌ Erreur du moteur IA : {error_str[:200]}. Réessayez dans un instant."
                    })

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} déconnecté du chatbot SOC.")
    except Exception as e:
        logger.error(f"Chatbot WebSocket error: {e}")
