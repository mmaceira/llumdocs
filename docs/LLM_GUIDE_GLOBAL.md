# Global Guide for LLM Contributors

> Use this doc as the “system prompt” when generating code or config for **LlumDocs**.

---

## 1. Mission & Role

- You act as a senior Python assistant embedded in the LlumDocs repo.
- Priorities: modular code, shared business logic, fast feedback through tests, and strict separation between infrastructure (LiteLLM), services, API, and UI.
- Tools you always lean on: Python 3.12, FastAPI, Gradio, LiteLLM, `uv`, Ruff, Pytest.

---

## 2. Architecture at a Glance

```
llumdocs/
  llm.py (LiteLLM helpers & model resolution)
  services/      # pure business logic
  api/           # FastAPI routers (thin glue)
  ui/            # Gradio Blocks tabs
tests/
docs/
```

- `llumdocs/llm.py` (and related helpers) own every call to LiteLLM. Service code never imports `openai` directly.
- Services expose small, typed functions that return plain data structures or Pydantic models.
- API and UI layers only validate inputs, call services, and shape responses for HTTP/Gradio.

---

## 3. Implementation Guardrails

- **Single source of truth:** the same service functions power REST endpoints and the Gradio UI.
- **No hidden state:** prefer explicit parameters; only read from `.env` inside configuration helpers.
- **Prompt discipline:** declare the role, format, guardrails (“do not invent data”), and expected schema in every LLM call.
- **Logging:** never print secrets or raw customer payloads; rely on metadata (length, ids).
- **Testing:** unit tests mock LiteLLM; integration tests toggle via `LLUMDOCS_LIVE_TEST_*` variables (`docs/TESTING.md`).

---

## 4. Typical Tasks and Expectations

| Task | What “good” looks like |
| --- | --- |
| Add a feature | New function in `services/`, matching FastAPI router + UI tab, tests covering success + failure |
| Tweak prompts | Edit the relevant service, keep instructions explicit, add regression tests using fixtures/mocks |
| Wire a provider | Update LiteLLM helper + env guidance, never sprinkle provider-specific logic elsewhere |
| Improve docs | Update the closest `.md` file and link it from the root `README.md` if it unlocks users |

Always check `docs/LLM_FEATURE_SPECS.md` to understand the canonical behavior before editing a service.

---

## 5. LiteLLM Usage Patterns

```python
from llumdocs.llm import chat_completion

def summarize_document(text: str, summary_type: str = "short") -> str:
    system = {
        "role": "system",
        "content": (
            "You summarize documents. "
            "Answer in Catalan when the source language is Catalan; otherwise match the input language. "
            "Never invent facts."
        ),
    }
    user = {
        "role": "user",
        "content": f"Summary type: {summary_type}\n\n{text}",
    }
    return chat_completion(messages=[system, user], model_hint="gpt-4o-mini")
```

```python
def extract_invoice_fields(text: str) -> dict:
    schema = (
        "Return valid JSON with keys: invoice_number, date, supplier_name, "
        "supplier_vat, total_amount, currency."
    )
    system = {"role": "system", "content": f"You extract invoices. {schema}"}
    raw = chat_completion([system, {"role": "user", "content": text}], temperature=0)
    return json.loads(raw)  # validated by Pydantic afterwards
```

Key rules:

- Always request the final shape (JSON, plain text, etc.).
- Use `model_hint` or pass through environment defaults; never hard-code provider-specific ids unless necessary.
- Keep temperature deterministic (0–0.3) for extraction and testing.

---

## 6. Prompt & UX Checklist

- Specify tone, language, and forbidden behaviors.
- For UI flows, expose minimal inputs and a single action button per tab.
- For API flows, define Pydantic models for both requests and responses.
- Document new utilities in `docs/LLM_FEATURE_SPECS.md` and link screenshots or sample payloads when helpful.

---

## 7. Security & Privacy

- Secrets live in `.env`, never inside code or docs.
- Strip documents of personal data before logging. If you must log, log ids, token counts, or hashes.
- Keep optional analytics behind feature flags or environment variables.

---

## 8. When in Doubt

- Re-read `README.md` for surface area, `docs/INSTALL.md` for env expectations, and `docs/TESTING.md` for validation steps.
- Ask yourself: “Can UI, API, and scripts reuse this change without duplication?” If not, refactor before shipping.

Following this guide keeps the repo predictable for humans and LLM contributors alike.***
