# LlumDocs Architecture

This document provides visual diagrams of the LlumDocs architecture and component communication flows. For detailed explanations of components, see:
- [LLM_GUIDE_GLOBAL.md](LLM_GUIDE_GLOBAL.md) - Architecture overview and development guidelines
- [INSTALL.md](INSTALL.md) - Setup, configuration, and environment variables
- [LLM_FEATURE_SPECS.md](LLM_FEATURE_SPECS.md) - Feature specifications and service contracts

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                      │
│  ┌──────────────────┐          ┌──────────────────┐         │
│  │   Gradio UI      │          │   FastAPI        │         │
│  │  (llumdocs.ui)   │          │  (llumdocs.api)  │         │
│  └────────┬─────────┘          └────────┬─────────┘         │
│           │                              │                   │
│           └──────────────┬───────────────┘                   │
└───────────────────────────┼───────────────────────────────────┘
                            │
┌───────────────────────────┼───────────────────────────────────┐
│                    Service Layer                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Translation, Text Transform, Image, Email Services  │   │
│  │              (llumdocs.services)                       │   │
│  └───────────────────────┬───────────────────────────────┘   │
└───────────────────────────┼───────────────────────────────────┘
                            │
┌───────────────────────────┼───────────────────────────────────┐
│              LLM Abstraction Layer                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              llumdocs.llm                            │   │
│  │  (Model resolution, LiteLLM wrapper, retry logic)     │   │
│  └───────────────────────┬───────────────────────────────┘   │
└───────────────────────────┼───────────────────────────────────┘
                            │
┌───────────────────────────┼───────────────────────────────────┐
│                    Provider Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   LiteLLM    │  │   Ollama     │  │   OpenAI     │        │
│  │  (Unified    │  │  (Local LLM) │  │  (Cloud LLM) │        │
│  │   Interface) │  │              │  │              │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│              Email Intelligence (Independent)                  │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Hugging Face Transformers (Zero-shot, Phishing,     │    │
│  │  Sentiment Analysis)                                  │    │
│  └──────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────┘
```

---

## Component Communication Overview

See [LLM_GUIDE_GLOBAL.md](LLM_GUIDE_GLOBAL.md) for detailed component descriptions and development guidelines.

---

## Communication Flow

### High-Level Request Flow

```
User Action
    │
    ├─→ [Gradio UI] ──┐
    │                  │
    └─→ [REST API] ────┼─→ [Service Layer]
                       │         │
                       │         ├─→ [LLM Tasks] → llumdocs.llm → LiteLLM → Ollama/OpenAI
                       │         │
                       │         └─→ [Email Intelligence] → Hugging Face Transformers
                       │
                       └─→ Response to User
```

### Detailed Translation Flow (Example)

```
1. User enters text in Gradio UI
   │
2. UI handler (components.py) calls translate_text()
   │
3. translation_service.py:
   │  - Validates languages
   │  - Builds prompt
   │  - Calls chat_completion() from llumdocs.llm
   │
4. llumdocs.llm.chat_completion():
   │  - Calls resolve_model() to determine provider
   │  - resolve_model() checks:
   │    * LLUMDOCS_DEFAULT_MODEL env var
   │    * Falls back to candidate list
   │    * Returns ModelConfig with model_id and kwargs
   │  - Calls litellm.completion() with retry logic
   │
5. LiteLLM:
   │  - Detects provider from model_id ("ollama/llama3.1:8b" or "gpt-4o-mini")
   │  - Formats request for provider
   │  - Sends HTTP request:
   │    * Ollama: POST http://localhost:11434/api/chat
   │    * OpenAI: POST https://api.openai.com/v1/chat/completions
   │
6. Provider processes request and returns response
   │
7. LiteLLM parses response and returns to llumdocs.llm
   │
8. llumdocs.llm returns text to service
   │
9. Service returns translated text to UI
   │
10. UI displays result to user
```

### Email Intelligence Flow (Example)

```
1. User enters email text in Gradio UI
   │
2. UI handler calls EmailIntelligenceService.analyze_email()
   │
3. email_intelligence_service.py:
   │  - Checks if email intelligence is enabled
   │  - Calls three functions:
   │    * classify_email() → _get_zero_shot_pipeline()
   │    * detect_phishing() → _get_phishing_pipeline()
   │    * analyze_sentiment() → _get_sentiment_pipeline()
   │
4. Pipeline loading (lazy, cached):
   │  - Checks if pipeline exists in module-level cache
   │  - If not, loads from Hugging Face:
   │    * Checks GPU availability
   │    * Downloads model if not cached
   │    * Creates pipeline (GPU if available, else CPU)
   │    * Caches pipeline for reuse
   │
5. Inference:
   │  - Truncates text to MAX_EMAIL_SEQUENCE_LENGTH (512 tokens)
   │  - Runs pipeline inference
   │  - Handles GPU OOM errors (falls back to CPU)
   │
6. Results:
   │  - ClassificationResult (labels, scores)
   │  - PhishingDetection (label, score, scores_by_label)
   │  - SentimentPrediction (label, score)
   │  - Combined into EmailInsights dataclass
   │
7. Returns EmailInsights to UI
   │
8. UI displays results to user
```

---

## Component Interaction Diagrams

### Translation Request (via API)

```
┌────────┐  POST /api/translate
│ Client │─────────────────────────┐
└────────┘                         │
                                   ▼
                          ┌─────────────────┐
                          │  FastAPI        │
                          │  /api/translate │
                          └────────┬────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │ translate_text()│
                          │ (service)       │
                          └────────┬────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │ chat_completion()│
                          │ (llumdocs.llm)  │
                          └────────┬────────┘
                                   │
                                   ▼
                          ┌─────────────────┐
                          │   LiteLLM       │
                          └────────┬────────┘
                                   │
                          ┌────────┴────────┐
                          │                 │
                    ┌─────▼─────┐    ┌─────▼─────┐
                    │  Ollama   │    │  OpenAI   │
                    │  :11434   │    │  API      │
                    └───────────┘    └───────────┘
                          │                 │
                          └────────┬────────┘
                                   │
                          ┌────────▼────────┐
                          │  Response      │
                          │  (JSON)        │
                          └────────────────┘
```

### Image Description (via UI)

```
┌────────┐
│  User  │ Uploads image
└───┬────┘
    │
    ▼
┌─────────────┐
│  Gradio UI  │
│  (image tab)│
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ describe_image() │
│ (service)        │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ vision_completion│
│ (llumdocs.llm)   │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐      ┌──────────────┐
│ resolve_vision_   │─────▶│ qwen3-vl:8b   │
│ model()          │      │ or o4-mini    │
└──────┬───────────┘      └──────┬───────┘
       │                         │
       ▼                         ▼
┌──────────────────┐      ┌──────────────┐
│   LiteLLM        │─────▶│  Provider    │
└──────────────────┘      └──────────────┘
       │
       ▼
┌──────────────────┐
│  Description     │
│  (displayed)     │
└──────────────────┘
```

---

## Deployment Architecture

### Development Setup

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       ├─→ http://localhost:7860 (Gradio UI)
       │
       └─→ http://localhost:8000 (FastAPI)
              │
              └─→ Services → llumdocs.llm → LiteLLM
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
              ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
              │  Ollama   │   │  OpenAI  │   │ Hugging   │
              │ localhost │   │  Cloud   │   │  Face     │
              │  :11434   │   │   API    │   │  Models   │
              └───────────┘   └───────────┘   └───────────┘
```

### Docker Compose Deployment

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   FastAPI    │  │   Gradio UI  │  │   Ollama     │ │
│  │  Container   │  │  Container   │  │  Container   │ │
│  │  Port 8000   │  │  Port 7860   │  │  Port 11434  │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                 │                  │         │
│         └─────────────────┼──────────────────┘         │
│                           │                            │
│                  ┌────────▼────────┐                   │
│                  │  Shared Volumes │                   │
│                  │  - HF cache     │                   │
│                  │  - Ollama models│                   │
│                  └─────────────────┘                   │
└─────────────────────────────────────────────────────────┘
         │
         └─→ External: OpenAI API (if configured)
```

**Key Points**:
- Services can run in separate containers or together
- Ollama can run in container or use host Ollama
- Hugging Face models cached in shared volume
- Environment variables control provider selection

---

## Model Resolution Flow

```
Service calls chat_completion(model_hint)
    │
    ▼
┌─────────────────────┐
│ resolve_model()     │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌─────────┐  ┌──────────────┐
│ Check   │  │ Check env var│
│ model_  │  │ LLUMDOCS_    │
│ hint    │  │ DEFAULT_MODEL│
└────┬────┘  └──────┬───────┘
     │             │
     └──────┬───────┘
            │
            ▼
    ┌───────────────┐
    │ Fallback list:│
    │ 1. ollama/     │
    │    llama3.1:8b │
    │ 2. gpt-4o-mini │
    │ 3. gpt-4o      │
    │ 4. gpt-3.5-    │
    │    turbo       │
    └───────┬───────┘
            │
    ┌───────┴───────┐
    │               │
    ▼               ▼
┌─────────┐   ┌──────────┐
│ Ollama? │   │ OpenAI?   │
│ Check   │   │ Check     │
│ enabled │   │ API_KEY   │
└────┬────┘   └─────┬─────┘
     │              │
     └──────┬───────┘
            │
            ▼
    ┌───────────────┐
    │ Return        │
    │ ModelConfig   │
    │ (model_id,    │
    │  kwargs)      │
    └───────────────┘
```

For environment variable details, see [INSTALL.md](INSTALL.md).

---

## Related Documentation

- [INSTALL.md](INSTALL.md) - Setup, configuration, and environment variables
- [LLM_GUIDE_GLOBAL.md](LLM_GUIDE_GLOBAL.md) - Architecture overview, component details, and development guidelines
- [LLM_FEATURE_SPECS.md](LLM_FEATURE_SPECS.md) - Feature specifications and service contracts
- [TESTING.md](TESTING.md) - Testing strategies and examples
