"""Task 2 Demo — compound scenario showing all 5 MCP tools in action.

Scenario: Customer checks order, initiates return, asks for product info,
checks inventory on a replacement, then gets escalated.
"""

import json
import sys
import os

# add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from task2_mcp.server import call_tool


def run_compound_demo():
    """Walk through a realistic multi-step customer interaction."""
    print("=" * 60)
    print("TASK 2: MCP TOOLS — COMPOUND DEMO SCENARIO")
    print("=" * 60)

    # step 1: customer checks their order
    print("\n--- Step 1: Customer checks order status ---")
    result = call_tool("get_order_status", order_id="ORD-000001")
    print(json.dumps(result, indent=2))

    # step 2: they want to return it
    print("\n--- Step 2: Customer initiates a return ---")
    result = call_tool("initiate_return", order_id="ORD-000001", reason="Product didn't match my skin type")
    print(json.dumps(result, indent=2))

    # step 3: they ask about a replacement product
    print("\n--- Step 3: Customer searches for a moisturizer ---")
    result = call_tool("get_product_info", query="moisturizer")
    print(f"Found {result.get('result_count', 0)} products")
    if result.get("results"):
        first = result["results"][0]
        print(f"Top result: {first['name']} (${first['price']}, SKU: {first['sku']})")

        # step 4: check if that product is in stock
        print(f"\n--- Step 4: Check inventory for {first['sku']} ---")
        inv = call_tool("check_inventory", sku=first["sku"])
        print(json.dumps(inv, indent=2))

    # step 5: customer gets frustrated, escalate
    print("\n--- Step 5: Customer escalates to human agent ---")
    result = call_tool("create_support_ticket",
                       customer_id="CUST-0001",
                       summary="Customer returned order ORD-000001, looking for replacement moisturizer for sensitive skin. Needs personal help choosing.",
                       priority="normal")
    print(json.dumps(result, indent=2))

    # show audit trail
    print("\n--- Audit Trail ---")
    audit_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "audit_log.jsonl")
    if os.path.exists(audit_path):
        with open(audit_path, "r") as f:
            lines = f.readlines()
        print(f"Total audit entries: {len(lines)}")
        for line in lines[-3:]:
            entry = json.loads(line)
            print(f"  {entry['timestamp'][:19]} | {entry['tool']} | {entry['status']}")

    print("\n" + "=" * 60)
    print("Demo complete. Audit log saved to audit_log.jsonl")
    print("=" * 60)


if __name__ == "__main__":
    run_compound_demo()
