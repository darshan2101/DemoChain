"""Task 5: NOVA Multi-Agent Platform — LangGraph orchestration (partial).

This is the capstone that wires Tasks 1-4 into a single LangGraph state machine.
Status: Core graph structure and routing logic implemented. Full end-to-end
execution is a work-in-progress.

Architecture:
  Customer Query -> Intent Classifier (Task 1)
    -> Route to specialist agent
    -> Brand Voice Layer (Task 4)
    -> Audit Trail Logger
    -> Response
"""

import json
import datetime
from typing import TypedDict, Optional
from pathlib import Path

# graph state shared across all nodes
class NovaState(TypedDict, total=False):
    query: str
    customer_id: str
    intent: str
    confidence: float
    sentiment_score: float
    tool_results: dict
    rag_context: str
    recommendation: dict
    draft_response: str
    final_response: str
    should_escalate: bool
    escalation_reason: str
    audit_trail: list
    error: Optional[str]


# --- Node Functions ---

def classify_intent_node(state: NovaState) -> NovaState:
    """Route the customer query to the right specialist using Task 1 prompts."""
    from task1_prompt_engineering import classify_intent, detect_escalation

    result = classify_intent(state["query"])
    intent = result.get("intent", "escalation")
    confidence = result.get("confidence", 0.0)

    # also check for frustration
    esc = detect_escalation(state["query"])
    severity = esc.get("severity_score", 0.0)

    trail = state.get("audit_trail", [])
    trail.append({
        "node": "classify_intent",
        "timestamp": datetime.datetime.now().isoformat(),
        "intent": intent,
        "confidence": confidence,
        "frustration_score": severity,
    })

    return {
        **state,
        "intent": intent,
        "confidence": confidence,
        "sentiment_score": severity,
        "should_escalate": severity >= 0.7 or intent == "escalation",
        "escalation_reason": esc.get("escalation_reason", ""),
        "audit_trail": trail,
    }


def handle_support_node(state: NovaState) -> NovaState:
    """Handle order/return queries using MCP tools (Task 2)."""
    from task2_mcp.client import MCPClient
    from nova_llm import call_llm_json

    client = MCPClient()
    intent = state["intent"]
    query = state["query"]

    # use LLM to extract parameters from the query
    extract_prompt = f"""Extract parameters from this customer message for the tool call.
Intent: {intent}
Message: {query}

Return JSON with the relevant fields:
- order_id (if mentioned, like ORD-XXXXXX)
- reason (if it's a return, why)
- product_query (if asking about a product)
Return {{"order_id": null, "reason": null, "product_query": null}} if not found."""

    try:
        params = call_llm_json("Extract parameters from customer message.", extract_prompt, temperature=0.1)
    except Exception:
        params = {"order_id": None, "reason": None, "product_query": None}

    tool_results = {}
    if intent == "order_status" and params.get("order_id"):
        tool_results = client.execute("get_order_status", order_id=params["order_id"])
    elif intent == "returns" and params.get("order_id"):
        reason = params.get("reason", "Customer requested return")
        tool_results = client.execute("initiate_return", order_id=params["order_id"], reason=reason)

    # generate a draft response based on tool results
    from nova_llm import call_llm, load_prompt
    system = load_prompt("nova_system_prompt_v1.txt")
    user_msg = f"Customer asked: {query}\n\nTool results: {json.dumps(tool_results, indent=2)}\n\nRespond to the customer based on this data."
    draft = call_llm(system, user_msg, temperature=0.5)

    trail = state.get("audit_trail", [])
    trail.append({
        "node": "handle_support",
        "timestamp": datetime.datetime.now().isoformat(),
        "tool_called": intent,
        "tool_results_summary": str(tool_results)[:200],
    })

    return {**state, "tool_results": tool_results, "draft_response": draft, "audit_trail": trail}


def handle_rag_node(state: NovaState) -> NovaState:
    """Answer product questions using RAG pipeline (Task 3)."""
    from rag_module import NovaRAG
    from nova_llm import call_llm, load_prompt

    rag = NovaRAG()
    rag.build_index()
    retrieval = rag.query(state["query"], top_k=3)

    system = load_prompt("nova_system_prompt_v1.txt")
    system += "\n\nUse this product information to answer:\n" + retrieval["context"]
    draft = call_llm(system, state["query"], temperature=0.3)

    trail = state.get("audit_trail", [])
    trail.append({
        "node": "handle_rag",
        "timestamp": datetime.datetime.now().isoformat(),
        "products_retrieved": [r["metadata"]["sku"] for r in retrieval["results"]],
    })

    return {**state, "rag_context": retrieval["context"], "draft_response": draft, "audit_trail": trail}


def handle_recommendation_node(state: NovaState) -> NovaState:
    """Generate personalized product recommendations."""
    from rag_module import NovaRAG
    from nova_llm import call_llm, load_prompt

    rag = NovaRAG()
    rag.build_index()
    retrieval = rag.query(state["query"], top_k=5)

    system = load_prompt("nova_system_prompt_v1.txt")
    system += "\n\nRecommend products from this catalog based on the customer's needs:\n" + retrieval["context"]
    draft = call_llm(system, state["query"], temperature=0.5)

    trail = state.get("audit_trail", [])
    trail.append({
        "node": "handle_recommendation",
        "timestamp": datetime.datetime.now().isoformat(),
        "candidates": [r["metadata"]["sku"] for r in retrieval["results"]],
    })

    return {**state, "draft_response": draft, "audit_trail": trail}


def handle_escalation_node(state: NovaState) -> NovaState:
    """Route to human agent with full context."""
    from task2_mcp.client import MCPClient

    client = MCPClient()
    ticket = client.execute(
        "create_support_ticket",
        customer_id=state.get("customer_id", "unknown"),
        summary=f"Escalated: {state['query'][:200]}. Reason: {state.get('escalation_reason', 'frustration detected')}",
        priority="high"
    )

    draft = f"I understand this is frustrating, and I want to make sure you get the help you deserve. I've escalated your case to our support team — a human agent will reach out to you shortly. Your reference number is {ticket.get('ticket_id', 'pending')}."

    trail = state.get("audit_trail", [])
    trail.append({
        "node": "handle_escalation",
        "timestamp": datetime.datetime.now().isoformat(),
        "ticket_id": ticket.get("ticket_id"),
        "priority": "high",
    })

    return {**state, "tool_results": ticket, "draft_response": draft, "should_escalate": True, "audit_trail": trail}


def brand_voice_node(state: NovaState) -> NovaState:
    """Rewrite the draft response in NOVA's brand voice (Task 4)."""
    from task4_brand_voice import evaluate_brand_voice

    # the draft is already generated with the NOVA system prompt,
    # so it should be mostly on-brand. evaluate and log the score.
    score = evaluate_brand_voice(state.get("draft_response", ""), state["query"])

    trail = state.get("audit_trail", [])
    trail.append({
        "node": "brand_voice",
        "timestamp": datetime.datetime.now().isoformat(),
        "brand_score": score.get("overall", 0),
    })

    return {**state, "final_response": state.get("draft_response", ""), "audit_trail": trail}


def audit_node(state: NovaState) -> NovaState:
    """Save the full audit trail for compliance."""
    traces_path = Path(__file__).parent / "nova_traces.json"

    trace = {
        "query": state["query"],
        "customer_id": state.get("customer_id", "unknown"),
        "intent": state.get("intent"),
        "confidence": state.get("confidence"),
        "escalated": state.get("should_escalate", False),
        "response_preview": state.get("final_response", "")[:200],
        "audit_trail": state.get("audit_trail", []),
        "timestamp": datetime.datetime.now().isoformat(),
    }

    # append to traces file
    traces = []
    if traces_path.exists():
        with open(traces_path, "r", encoding="utf-8") as f:
            traces = json.load(f)
    traces.append(trace)
    with open(traces_path, "w", encoding="utf-8") as f:
        json.dump(traces, f, indent=2, ensure_ascii=False)

    return state


# --- Routing Logic ---

def route_by_intent(state: NovaState) -> str:
    """Decide which agent handles this query based on classified intent."""
    if state.get("should_escalate"):
        return "escalation"
    intent = state.get("intent", "escalation")
    routing = {
        "order_status": "support",
        "returns": "support",
        "product_recommendation": "recommendation",
        "sizing": "rag",
        "ingredient_query": "rag",
        "escalation": "escalation",
    }
    return routing.get(intent, "escalation")


# --- Graph Builder ---

def build_nova_graph():
    """Build the LangGraph state machine for NOVA support."""
    try:
        from langgraph.graph import StateGraph, END

        graph = StateGraph(NovaState)

        # add all nodes
        graph.add_node("classify_intent", classify_intent_node)
        graph.add_node("support", handle_support_node)
        graph.add_node("rag", handle_rag_node)
        graph.add_node("recommendation", handle_recommendation_node)
        graph.add_node("escalation", handle_escalation_node)
        graph.add_node("brand_voice", brand_voice_node)
        graph.add_node("audit", audit_node)

        # entry point
        graph.set_entry_point("classify_intent")

        # conditional routing after intent classification
        graph.add_conditional_edges("classify_intent", route_by_intent, {
            "support": "support",
            "rag": "rag",
            "recommendation": "recommendation",
            "escalation": "escalation",
        })

        # all specialist nodes feed into brand voice
        graph.add_edge("support", "brand_voice")
        graph.add_edge("rag", "brand_voice")
        graph.add_edge("recommendation", "brand_voice")
        graph.add_edge("escalation", "brand_voice")

        # brand voice -> audit -> end
        graph.add_edge("brand_voice", "audit")
        graph.add_edge("audit", END)

        return graph.compile()
    except ImportError:
        print("LangGraph not installed - graph build skipped")
        return None


def run_query(query, customer_id="CUST-0001"):
    """Run a single customer query through the full NOVA pipeline."""
    graph = build_nova_graph()
    if graph is None:
        print("Cannot run without LangGraph installed")
        return None

    initial_state = {
        "query": query,
        "customer_id": customer_id,
        "audit_trail": [],
    }

    result = graph.invoke(initial_state)
    return result
