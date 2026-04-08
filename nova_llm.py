"""NOVA LLM client — handles OpenRouter and Groq calls with fallback."""

import os
import json
import openai
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

# provider config (keys loaded from env, never logged)
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
GROQ_BASE = "https://api.groq.com/openai/v1"

# default models per provider
OPENROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
GROQ_MODEL = "llama-3.3-70b-versatile"


def _get_client(provider="openrouter"):
    """Build an OpenAI-compatible client for the given provider."""
    if provider == "groq":
        return openai.OpenAI(
            base_url=GROQ_BASE,
            api_key=os.getenv("GROQ_API_KEY")
        )
    return openai.OpenAI(
        base_url=OPENROUTER_BASE,
        api_key=os.getenv("OPENROUTER_API_KEY")
    )


def call_llm(system_prompt, user_message, temperature=0.3, provider="openrouter", model=None):
    """Call an LLM with fallback: try OpenRouter first, then Groq."""
    providers = [provider, "groq"] if provider != "groq" else ["groq", "openrouter"]

    for p in providers:
        try:
            client = _get_client(p)
            m = model or (OPENROUTER_MODEL if p == "openrouter" else GROQ_MODEL)
            resp = client.chat.completions.create(
                model=m,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )
            content = resp.choices[0].message.content
            if content is None:
                raise ValueError(f"{m} returned empty response")
            return content.strip()
        except Exception as e:
            print(f"  [{p}] failed: {e}")
            continue

    raise RuntimeError("All LLM providers failed")


def call_llm_json(system_prompt, user_message, **kwargs):
    """Call LLM and parse the response as JSON."""
    raw = call_llm(system_prompt, user_message, **kwargs)
    # strip markdown fences if present
    cleaned = raw.replace("```json", "").replace("```", "").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start != -1 and end > 0:
        cleaned = cleaned[start:end]
    return json.loads(cleaned)


def load_prompt(name):
    """Load a prompt file from the prompts/ directory."""
    prompt_dir = Path(__file__).parent / "prompts"
    path = prompt_dir / name
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8")
