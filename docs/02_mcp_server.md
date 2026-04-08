# Task 2: MCP Server — NOVA Backend Tool Integration

## What This Does

5 backend tools accessible via the Model Context Protocol (MCP). Instead of each AI agent knowing how to query databases directly, they call these tools through a clean interface. Every call is audit-logged for legal compliance.

## The Tools

| Tool | What It Does | When It's Called |
|------|-------------|-----------------|
| `get_order_status` | Looks up order tracking, status, carrier info | Customer asks "where's my order?" |
| `initiate_return` | Starts return process, generates shipping label | Customer wants to send something back |
| `get_product_info` | Searches catalog by SKU or keyword | Customer asks about a product |
| `check_inventory` | Real-time stock check by SKU and size | Before recommending a product |
| `create_support_ticket` | Escalates to human with full context | Frustrated customer or complex issue |

## Architecture

```
LLM Agent
    |
    v
MCPClient.execute("get_order_status", order_id="ORD-123")
    |
    v
MCP Server (server.py)
    |---> Reads from nova_mock_db.json
    |---> Writes to audit_log.jsonl
    |
    v
Returns structured result to agent
```

### Why MCP instead of direct function calls?
- **Separation of concerns**: tools don't know about LLMs, LLMs don't know about databases
- **Audit trail built in**: every tool call is logged automatically with timestamp, inputs, outputs
- **Swappable backends**: mock DB today, real API tomorrow — agents don't change
- **Standard protocol**: MCP is becoming the standard for LLM-tool integration

## Audit Trail

Every tool call produces a JSONL entry:
```json
{
  "timestamp": "2026-04-08T12:00:00",
  "tool": "get_order_status",
  "inputs": {"order_id": "ORD-000123"},
  "output_summary": "{\"status\": \"shipped\", ...}",
  "status": "success"
}
```

This satisfies NOVA's legal requirement: every AI decision that touches customer data is traceable.

## How to Run

```bash
# run the compound demo scenario
python task2_mcp/demo.py
```

The demo walks through a full customer journey: check order → return it → search for replacement → check stock → escalate to human.

## Files

| File | Purpose |
|------|---------|
| `task2_mcp/server.py` | 5 tools + audit logging |
| `task2_mcp/client.py` | Client wrapper for agents |
| `task2_mcp/demo.py` | Compound scenario demo |
| `audit_log.jsonl` | Generated audit trail |
