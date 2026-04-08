# Task 4: Fine-Tuning — NOVA Brand Voice Model

## What This Does

NOVA needs every customer response to feel warm, friendly, and on-brand. A generic LLM sounds corporate. Fine-tuning teaches a small model NOVA's specific communication style so every response feels like it came from the same person.

## Approach: QLoRA

We use QLoRA (Quantized Low-Rank Adaptation) because:
- **4-bit quantization** — fits a 3.8B parameter model in ~3GB VRAM (Colab Free T4 has 16GB)
- **LoRA adapters** — only trains ~1% of parameters, fast and cheap
- **No full model copy** — adapters are tiny (~10MB) vs full model weights (~7GB)

```
Base Model (frozen, 4-bit quantized)
    |
    v
LoRA Adapters (tiny trainable layers)
    |
    v
Fine-tuned NOVA voice model
```

## Training Data Strategy

We generate training data using our existing LLM (OpenRouter/Groq):
1. Take 50 sample customer queries from our mock tickets
2. Generate ideal NOVA-style responses using the COSTAR prompt (Task 1)
3. Create training pairs: {customer_message, nova_response}

This is a legitimate approach called "distillation" — using a larger model to teach a smaller model a specific behavior.

## Brand Voice Characteristics

NOVA's brand voice is:
- **Warm**: "Hey! Great question about that serum" (not "Dear valued customer")
- **Knowledgeable**: specific product details, not vague claims
- **Proactive**: suggests next steps without being asked
- **Concise**: 2-4 sentences, not paragraphs
- **Lightly playful**: occasional emoji, casual phrasing

## Evaluation

We compare base model vs fine-tuned model on 10 test prompts:
- **Brand alignment score**: does the response sound like NOVA?
- **Helpfulness score**: does it actually answer the question?
- **Conciseness**: is it appropriately short?

Evaluation uses our LLM as judge — same approach used in LMSYS Chatbot Arena.

## How to Run

The fine-tuning notebook is designed for Google Colab Free tier:
1. Open `task4_finetune.ipynb` in Colab
2. Set runtime to T4 GPU
3. Add your API keys in the secrets
4. Run all cells

## Files

| File | Purpose |
|------|---------|
| `task4_finetune.ipynb` | Complete training notebook |
| `task4_brand_voice.py` | Brand voice generation + evaluation module |
