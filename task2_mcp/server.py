"""Task 2: MCP Server — 5 backend tools for NOVA customer support.

Implements the Model Context Protocol (MCP) server with tools for:
- get_order_status: look up order tracking info
- initiate_return: start a return process
- get_product_info: query product catalog
- check_inventory: check stock by SKU + size
- create_support_ticket: escalate to human agent

Every tool call is logged to audit_log.jsonl for compliance.
"""

import json
import datetime
from pathlib import Path

# load the mock database
DB_PATH = Path(__file__).parent.parent / "nova_mock_db.json"
AUDIT_LOG_PATH = Path(__file__).parent.parent / "audit_log.jsonl"


def _load_db():
    """Load the mock database from disk."""
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _log_audit(tool_name, inputs, output, status="success"):
    """Append an audit entry to the JSONL log file."""
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "tool": tool_name,
        "inputs": inputs,
        "output_summary": str(output)[:500],
        "status": status,
    }
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


# --- Tool 1: Order Status ---

def get_order_status(order_id):
    """Look up order by ID and return status, tracking, and delivery info."""
    db = _load_db()
    for order in db["orders"]:
        if order["order_id"] == order_id:
            result = {
                "order_id": order["order_id"],
                "status": order["status"],
                "order_date": order["order_date"],
                "total": order["total"],
                "items": [item["name"] for item in order["items"]],
                "estimated_delivery": order.get("estimated_delivery"),
                "tracking_number": order.get("tracking_number"),
                "carrier": order.get("carrier"),
                "delivered_date": order.get("delivered_date"),
            }
            _log_audit("get_order_status", {"order_id": order_id}, result)
            return result

    _log_audit("get_order_status", {"order_id": order_id}, "not found", "not_found")
    return {"error": f"Order {order_id} not found"}


# --- Tool 2: Initiate Return ---

def initiate_return(order_id, reason):
    """Start a return process for the given order."""
    db = _load_db()
    for order in db["orders"]:
        if order["order_id"] == order_id:
            if order["status"] == "returned":
                result = {"error": "Return already in progress for this order"}
                _log_audit("initiate_return", {"order_id": order_id, "reason": reason}, result, "rejected")
                return result

            result = {
                "return_id": f"RET-{order_id.split('-')[1]}",
                "order_id": order_id,
                "status": "return_initiated",
                "reason": reason,
                "return_label_url": f"https://nova.com/returns/{order_id}/label.pdf",
                "refund_estimate": f"{order['total']:.2f}",
                "instructions": "Pack items in original packaging. Drop at any FedEx location within 14 days."
            }
            _log_audit("initiate_return", {"order_id": order_id, "reason": reason}, result)
            return result

    _log_audit("initiate_return", {"order_id": order_id, "reason": reason}, "not found", "not_found")
    return {"error": f"Order {order_id} not found"}


# --- Tool 3: Product Info ---

def get_product_info(query):
    """Search for a product by SKU or keyword and return details."""
    db = _load_db()
    results = []

    for product in db["products"]:
        # match on SKU or keyword in name/type/category
        if (query.upper() in product["sku"] or
            query.lower() in product["name"].lower() or
            query.lower() in product["type"].lower() or
            query.lower() in product["category"].lower()):
            results.append(product)

    if not results:
        _log_audit("get_product_info", {"query": query}, "no results", "not_found")
        return {"error": f"No products matching '{query}'", "results": []}

    # return top 5 matches
    top = results[:5]
    _log_audit("get_product_info", {"query": query}, f"{len(top)} results")
    return {"query": query, "result_count": len(results), "results": top}


# --- Tool 4: Check Inventory ---

def check_inventory(sku, size=None):
    """Check if a product is in stock, optionally for a specific size."""
    db = _load_db()
    for product in db["products"]:
        if product["sku"] == sku:
            result = {
                "sku": sku,
                "name": product["name"],
                "in_stock": product["in_stock"],
                "price": product["price"],
            }
            if size and "available_sizes" in product:
                result["size_available"] = size in product["available_sizes"]
                result["all_sizes"] = product["available_sizes"]
            elif size:
                result["size_available"] = True  # non-sized products always fit

            _log_audit("check_inventory", {"sku": sku, "size": size}, result)
            return result

    _log_audit("check_inventory", {"sku": sku, "size": size}, "not found", "not_found")
    return {"error": f"Product {sku} not found"}


# --- Tool 5: Create Support Ticket ---

def create_support_ticket(customer_id, summary, priority="normal"):
    """Create an escalation ticket for a human agent."""
    ticket_id = f"ESC-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    result = {
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "summary": summary,
        "priority": priority,
        "status": "open",
        "created_at": datetime.datetime.now().isoformat(),
        "assigned_to": "next_available_agent",
        "message": f"Your request has been escalated. A human agent will contact you shortly. Reference: {ticket_id}"
    }
    _log_audit("create_support_ticket", {"customer_id": customer_id, "summary": summary, "priority": priority}, result)
    return result


# --- MCP Tool Registry ---

TOOLS = {
    "get_order_status": {
        "function": get_order_status,
        "description": "Look up order status, tracking, and delivery information",
        "parameters": {"order_id": "string (required) — NOVA order ID like ORD-000123"},
    },
    "initiate_return": {
        "function": initiate_return,
        "description": "Start a return process and generate a return shipping label",
        "parameters": {
            "order_id": "string (required) — NOVA order ID",
            "reason": "string (required) — why the customer is returning",
        },
    },
    "get_product_info": {
        "function": get_product_info,
        "description": "Search the product catalog by SKU or keyword",
        "parameters": {"query": "string (required) — SKU or search keyword"},
    },
    "check_inventory": {
        "function": check_inventory,
        "description": "Check real-time stock availability for a product",
        "parameters": {
            "sku": "string (required) — product SKU",
            "size": "string (optional) — size to check",
        },
    },
    "create_support_ticket": {
        "function": create_support_ticket,
        "description": "Escalate to a human agent by creating a support ticket",
        "parameters": {
            "customer_id": "string (required) — customer ID",
            "summary": "string (required) — issue summary with full context",
            "priority": "string (optional) — normal or high",
        },
    },
}


def call_tool(tool_name, **kwargs):
    """Execute an MCP tool by name with the given arguments."""
    if tool_name not in TOOLS:
        return {"error": f"Unknown tool: {tool_name}"}
    return TOOLS[tool_name]["function"](**kwargs)


def get_tool_definitions():
    """Return tool definitions in the format LLMs expect for function calling."""
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": info["description"],
                "parameters": info["parameters"],
            }
        }
        for name, info in TOOLS.items()
    ]
