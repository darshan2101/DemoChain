# Task 5: Multi-Agent Platform — NOVA AI Support System (Partial)

## Status: Core Architecture Implemented, Full E2E Testing WIP

The LangGraph state machine is built with all nodes and routing logic. Tasks 1-4 are wired in as specialist agents. Full end-to-end execution across diverse scenarios is still being validated.

## Architecture

```
Customer Query
      |
      v
[classify_intent] -- Task 1 prompts (CoT + escalation detection)
      |
      |-- intent: order_status/returns --> [support] -- Task 2 MCP tools
      |-- intent: sizing/ingredient     --> [rag] -- Task 3 RAG pipeline
      |-- intent: recommendation        --> [recommendation] -- RAG + persona
      |-- intent: escalation/frustrated --> [escalation] -- human handoff
      |
      v
[brand_voice] -- Task 4 brand consistency check
      |
      v
[audit] -- logs everything to nova_traces.json
      |
      v
Final Response
```

## State Machine

The graph uses a typed state dict passed through every node:

```python
class NovaState(TypedDict):
    query: str              # customer's message
    customer_id: str        # session identifier
    intent: str             # classified intent
    confidence: float       # classification confidence
    sentiment_score: float  # frustration level (0-1)
    tool_results: dict      # MCP tool outputs
    rag_context: str        # retrieved product knowledge
    draft_response: str     # pre-brand-voice answer
    final_response: str     # brand-voice answer
    should_escalate: bool   # escalation flag
    audit_trail: list       # every decision logged
```

## What's Working
- Graph structure compiles and routes correctly
- All node functions defined and individually tested via Tasks 1-4
- Conditional routing based on intent classification
- Audit trail captures every node's decision

## What's WIP
- Full end-to-end demo across 5 diverse scenarios
- Conversation memory (multi-turn support)
- LangGraph visualization export (nova_agent_graph.png)

## Files

| File | Purpose |
|------|---------|
| `task5_nova_platform.py` | LangGraph state machine with all nodes |
