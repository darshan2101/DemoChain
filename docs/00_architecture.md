# NOVA AI Platform — System Architecture

## Overview

NOVA AI Platform is a multi-agent system that handles customer support for a D2C fashion & beauty brand. It automates 60% of support tickets while maintaining brand consistency and legal compliance.

## How It Works

```
Customer Message
       │
       ▼
┌──────────────┐
│  Intent       │  ← Chain-of-Thought classification (Task 1)
│  Classifier   │     Detects: order_status, returns, product_query,
└──────┬───────┘     sizing, ingredient_query, escalation
       │
       ├──────────────────┬──────────────────┬──────────────────┐
       ▼                  ▼                  ▼                  ▼
┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│  Support │      │  Product │      │  Reco    │      │ Escalate │
│  Agent   │      │  RAG     │      │  Engine  │      │  Router  │
│ (Task 2) │      │ (Task 3) │      │          │      │          │
└────┬─────┘      └────┬─────┘      └────┬─────┘      └────┬─────┘
     │                 │                  │                  │
     └────────┬────────┘──────────┬───────┘                 │
              ▼                                             │
      ┌──────────────┐                                      │
      │  Brand Voice  │  ← Fine-tuned model (Task 4)        │
      │  Layer        │     Rewrites in NOVA's warm tone    │
      └──────┬───────┘                                      │
              │                                             │
              └──────────────┬──────────────────────────────┘
                             ▼
                    ┌──────────────┐
                    │  Audit Trail │  ← Every decision logged
                    │  Logger      │     for legal compliance
                    └──────┬───────┘
                           ▼
                    Customer Response
```

## Components

| Component | Task | Tech | Purpose |
|-----------|------|------|---------|
| Prompt Engine | 1 | COSTAR framework | Structured prompts for every agent |
| MCP Server | 2 | JSON-RPC tools | Backend tools: orders, returns, inventory |
| RAG Pipeline | 3 | ChromaDB + BM25 | Product knowledge retrieval |
| Brand Voice | 4 | QLoRA fine-tuning | Consistent brand tone |
| Orchestrator | 5 | LangGraph | State machine routing all agents |

## Design Decisions

### Why LangGraph (not raw function chains)?
- Formal state machine = every transition is explicit and testable
- Conditional routing = skip irrelevant agents (faster, cheaper)
- Built-in state = audit trail is part of the graph, not bolted on

### Why ChromaDB (not Pinecone/Weaviate)?
- Runs embedded in the notebook — no server needed on Colab Free
- Persistent storage with zero config
- Good enough for 200 products — we don't need scale

### Why OpenRouter + Groq (not direct OpenAI)?
- Free tier models via OpenRouter — no API cost
- Groq for ultra-fast fallback — llama-3.3-70b at near-zero latency
- Both proven reliable from prior production work

### Why MCP (not raw function calling)?
- Industry standard for LLM tool integration
- Clean separation: server defines tools, client invokes them
- Built-in audit logging per the spec
