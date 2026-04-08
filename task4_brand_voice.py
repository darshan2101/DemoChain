"""Task 4: Brand Voice — generate training data and evaluate brand consistency.

This module handles:
1. Generating NOVA-style training data from customer queries
2. Evaluating brand voice quality of responses
3. Comparing base vs fine-tuned model outputs
"""

import json
import time
import sys
from pathlib import Path
from nova_llm import call_llm, call_llm_json, load_prompt


TRAINING_DATA_PATH = Path(__file__).parent / "brand_voice_training.json"


def generate_training_pair(customer_message):
    """Generate an ideal NOVA brand voice response for a customer message."""
    system = load_prompt("nova_system_prompt_v1.txt")
    system += """

IMPORTANT: Generate a response that perfectly embodies NOVA's brand voice:
- Warm and friendly, not corporate
- Start with a casual acknowledgment
- Be specific and helpful
- End with a proactive next step
- Keep it to 2-4 sentences
- Use 1 emoji max"""

    response = call_llm(system, customer_message, temperature=0.7)
    return {"customer_message": customer_message, "nova_response": response}


def generate_training_dataset(count=50):
    """Generate a dataset of NOVA brand voice training pairs."""
    db_path = Path(__file__).parent / "nova_mock_db.json"
    with open(db_path, "r", encoding="utf-8") as f:
        db = json.load(f)

    # use real ticket messages as source queries
    messages = [t["message"] for t in db["support_tickets"]]

    # also add some generic product queries
    extra = [
        "What's your best-selling moisturizer?",
        "I have oily skin, what foundation should I try?",
        "Are your products cruelty-free?",
        "Do you ship to Canada?",
        "How long does shipping usually take?",
        "Can I change my order after placing it?",
        "What's your return policy?",
        "Do you have a loyalty program?",
        "Is there a student discount?",
        "What's new this season?",
    ]
    messages.extend(extra)
    messages = messages[:count]

    print(f"Generating {len(messages)} training pairs...")
    pairs = []
    for i, msg in enumerate(messages):
        try:
            pair = generate_training_pair(msg)
            pairs.append(pair)
            if (i + 1) % 10 == 0:
                print(f"  Generated {i+1}/{len(messages)}")
        except Exception as e:
            print(f"  Skipped message {i+1}: {e}")

    with open(TRAINING_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(pairs, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(pairs)} training pairs to {TRAINING_DATA_PATH}")
    return pairs


def evaluate_brand_voice(response, customer_message):
    """Score a response on NOVA brand voice alignment (0-1)."""
    system = """You are evaluating whether a customer support response matches NOVA's brand voice.

NOVA's voice is: warm, friendly, knowledgeable, concise, slightly playful, uses casual-professional language.

Score the response on these criteria:
1. Warmth (0-1): Does it feel human and friendly?
2. Helpfulness (0-1): Does it actually address the customer's need?
3. Conciseness (0-1): Is it appropriately brief (2-4 sentences)?
4. Brand fit (0-1): Would this feel at home on NOVA's website?

Return JSON only:
{"warmth": 0.0, "helpfulness": 0.0, "conciseness": 0.0, "brand_fit": 0.0, "overall": 0.0, "feedback": "..."}"""

    user = f"Customer message: {customer_message}\n\nResponse to evaluate: {response}"
    return call_llm_json(system, user, temperature=0.1)


def run_evaluation():
    """Evaluate brand voice quality on test messages."""
    print("=" * 60)
    print("TASK 4: BRAND VOICE EVALUATION")
    print("=" * 60)

    test_messages = [
        "Where is my order ORD-000123?",
        "What moisturizer is good for sensitive skin?",
        "I want to return my purchase.",
        "Do you have this hoodie in size L?",
        "What ingredients are in your vitamin C serum?",
    ]

    scores = []
    for i, msg in enumerate(test_messages):
        print(f"\nCustomer: {msg}")

        # generate response using our system prompt
        system = load_prompt("nova_system_prompt_v1.txt")
        response = call_llm(system, msg, temperature=0.5)
        # safe print for Windows console (strips emoji)
        safe_resp = response[:150].encode('ascii', 'replace').decode('ascii')
        print(f"Response: {safe_resp}...")

        # evaluate it
        time.sleep(2)  # avoid rate limits between calls
        eval_result = evaluate_brand_voice(response, msg)
        print(f"Brand voice score: {eval_result.get('overall', 0)}")
        scores.append(eval_result)

        if i < len(test_messages) - 1:
            time.sleep(2)

    avg = sum(s.get("overall", 0) for s in scores) / len(scores) if scores else 0
    print(f"\nAverage brand voice score: {avg:.2f}")
    print("=" * 60)
    return scores


if __name__ == "__main__":
    run_evaluation()
