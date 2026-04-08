# NOVA AI Platform

> AI-powered customer support and personalization platform for NOVA — a D2C fashion & beauty brand.

## What This Is

A multi-agent AI system that:
- **Automates 60% of support tickets** — order status, returns, product FAQs
- **Answers product questions** via RAG over the product catalog
- **Recommends products** based on customer profile and skin type
- **Speaks in NOVA's brand voice** using a fine-tuned model
- **Escalates to humans** when frustration is detected
- **Logs every decision** for legal audit compliance

## Quick Start

```bash
# 1. Clone and install
git clone <repo-url>
cd nova-ai-platform
pip install -r requirements.txt

# 2. Set up API keys
cp .env.example .env
# Edit .env with your OpenRouter and Groq keys

# 3. Generate mock data
python scripts/generate_mock_data.py

# 4. Run the platform demo
python task5_demo.py
```

## Project Structure

```
├── README.md                          ← you are here
├── requirements.txt                   ← all dependencies pinned
├── .env.example                       ← API key template
├── nova_mock_db.json                  ← synthetic customer/order/product data
│
├── prompts/                           ← Task 1: Prompt Engineering
│   ├── nova_system_prompt_v1.txt
│   ├── intent_classifier_v1.txt
│   └── escalation_prompt_v1.txt
│
├── task1_prompt_engineering.ipynb      ← Task 1 notebook
│
├── task2_mcp/                         ← Task 2: MCP Server
│   ├── server.py
│   ├── client.py
│   └── demo.py
│
├── task3_rag_pipeline.ipynb           ← Task 3 notebook
├── rag_module.py                      ← importable RAG module (used by Task 5)
│
├── task4_finetune.ipynb               ← Task 4 notebook
│
├── task5_nova_platform.py             ← Task 5: LangGraph multi-agent system
├── task5_demo.py                      ← Task 5 demo runner
│
├── docs/                              ← design documentation per module
├── scripts/                           ← utility scripts
├── evaluation_report.json             ← RAGAS results
├── audit_log.jsonl                    ← MCP audit trail
└── nova_traces.json                   ← agent decision audit trails
```

## Tasks

| Task | Focus | Status |
|------|-------|--------|
| 1 | Prompt Engineering — COSTAR + CoT intent classifier | 🔨 |
| 2 | MCP Server — 5 backend tools + audit logging | 🔨 |
| 3 | RAG Pipeline — ChromaDB + hybrid search + RAGAS | 🔨 |
| 4 | Fine-Tuning — QLoRA brand voice model | 🔨 |
| 5 | Multi-Agent Platform — LangGraph orchestration | 🔨 |

## Shareable Links

- **GitHub Repository:** `<link>`
- **Colab Notebooks:** `<links>`

## Tech Stack

- **LLMs:** OpenRouter (free tier models) + Groq (llama-3.3-70b)
- **Orchestration:** LangGraph
- **RAG:** ChromaDB + sentence-transformers + BM25
- **Fine-tuning:** QLoRA via PEFT + TRL
- **Backend Tools:** MCP (Model Context Protocol)
