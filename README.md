# Framing Lens

> An academic tool for studying political framing in Indian news. It generates fact-checked, clearly labelled pro-government perspectives on news stories.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688)
![OpenAI](https://img.shields.io/badge/LLM-OpenAI-412991)

Framing Lens takes a news headline, an article, or both. It shows how the same facts can be presented from a pro-government viewpoint, and it makes the rhetoric visible: each output names the framing technique it uses, lists the claims a reader should verify, and reports any fabricated facts or false cause-and-effect links that the automated fact-guard removed.

The project supports research and teaching on media literacy and political communication. **All output is labelled as opinion, not news reporting.**

---

## Table of Contents

- [Features](#features)
- [How It Works](#how-it-works)
- [Framing Techniques](#framing-techniques)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Responsible Use](#responsible-use)
- [Roadmap](#roadmap)

---

## Features

- **Three-stage LLM pipeline:** *Analyse → Frame → Guard*. Each stage is a separate model call with its own prompt.
- **Named framing techniques:** every perspective uses one of six defined, legitimate rhetorical techniques and states which one.
- **Built-in fact-guard:** a separate audit pass flags fabricated facts, false causation, impossible chronology and unverified claims, then rewrites the draft without them.
- **Full transparency:** the response includes a neutral summary, the technique used, the claims that need citations, an "honest limit" statement, every issue the guard removed, and the raw draft.
- **Simple web interface:** one HTML page with light and dark themes. No build step.
- **Tests that run offline:** the test suite uses a stubbed LLM, so no API key is needed.

---

## How It Works

```
                ┌─────────────────────────────┐
                │  Browser (static/index.html)│
                └──────────────┬──────────────┘
                               │  POST /api/frame { headline, content }
                               ▼
                ┌─────────────────────────────┐
                │     FastAPI  (app/main.py)  │
                └──────────────┬──────────────┘
                               ▼
        ┌──────────────── Pipeline (app/pipeline.py) ───────────────┐
        │                                                           │
        │  1. ANALYSE ─► summary, category, tone, facts, causes     │
        │        │                                                  │
        │        ▼                                                  │
        │  2. FRAME   ─► technique + pro-government draft           │
        │        │                                                  │
        │        ▼                                                  │
        │  3. GUARD   ─► issues list + revised, corrected output    │
        │                                                           │
        └───────────────────────────┬───────────────────────────────┘
                                    ▼
                    OpenAI Chat Completions (JSON mode)
```

| Stage | Purpose | Output |
|-------|---------|--------|
| **1. Analyse** | Understand the news item and extract *only* what the text actually says. | Neutral summary, category, tone toward the government, stated facts, stated causes, date hints |
| **2. Frame** | Write the strongest honest pro-government perspective, grounded in the extracted facts. | Technique, headline, 120–200 word perspective, key points, claims needing citation, honest limit |
| **3. Guard** | Audit every sentence of the draft against the extracted facts and the public record. | Issues found, verdict (`pass` / `revised`), corrected headline, perspective and key points |

### What the fact-guard catches

| Issue type | Description |
|------------|-------------|
| `fabricated` | A number, quote, date or source that is neither in the article nor widely documented. |
| `false_causation` | Says or implies that X caused Y without support. |
| `chronology` | Links events in a way their timing makes impossible (e.g. blaming a 2026 event on 2016 demonetisation). |
| `unverified` | A plausible general-knowledge claim that still needs a citation. |

---

## Framing Techniques

| Key | Technique | Description |
|-----|-----------|-------------|
| `context_framing` | Context framing | Places the news in a wider context (global trends, other countries, past periods). |
| `juxtaposition` | Juxtaposition | Places a real government achievement next to the news *without* claiming it caused the news. |
| `long_term_framing` | Long-term framing | Presents short-term pain as part of a publicly stated long-term policy goal. |
| `external_attribution` | External attribution | Attributes the problem to genuine external factors (global markets, geopolitics, weather). |
| `silver_lining` | Silver lining | Highlights whatever in the story genuinely reflects well on the government or country. |
| `credit_claiming` | Credit claiming | For positive news, links it to government policy only where that link is publicly documented. |

News items are sorted into these categories: `economy`, `prices_inflation`, `security_defence`, `foreign_policy`, `infrastructure`, `social_welfare`, `governance`, `environment` and `other`.

---

## Project Structure

```
framing-lens/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app: routes, request validation, error handling
│   ├── pipeline.py      # Analyse → Frame → Guard pipeline and OpenAI client wrapper
│   ├── prompts.py       # System prompts and framing-technique definitions
│   └── static/
│       └── index.html   # Single-page web interface
├── tests/
│   └── test_pipeline.py # Offline tests using a stubbed LLM
├── requirements.txt
└── README.md
```

---

## Getting Started

### Prerequisites

- Python **3.10** or newer
- An [OpenAI API key](https://platform.openai.com/api-keys)

### Installation

```bash
git clone https://github.com/sachiin044/framing-lens.git
cd framing-lens

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### Run the app

Set your API key:

```bash
export OPENAI_API_KEY=sk-...          # macOS / Linux
```

```powershell
$env:OPENAI_API_KEY = "sk-..."        # Windows PowerShell
```

Start the server:

```bash
uvicorn app.main:app --reload
```

Then open **http://localhost:8000** in your browser, paste a headline or an article, and click **Generate perspective**. Each request makes three model calls and usually takes 10 to 20 seconds.

> **Never commit your API key.** `.env` is already listed in `.gitignore`.

---

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | – | Your OpenAI API key. Without it, `/api/frame` returns `503`. |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | The chat model used for all three pipeline stages. |

---

## API Reference

### `GET /health`

Health check.

```json
{ "status": "ok", "llm_configured": true }
```

### `POST /api/frame`

Runs the full pipeline on a news item. Provide `headline`, `content`, or both.

**Request body**

| Field | Type | Limit | Description |
|-------|------|-------|-------------|
| `headline` | string, optional | 500 chars | The news headline |
| `content` | string, optional | 12,000 chars | The article body |

```bash
curl -X POST http://localhost:8000/api/frame \
  -H "Content-Type: application/json" \
  -d '{"headline": "Petrol prices rise by ₹2 per litre"}'
```

**Response (abridged)**

```json
{
  "label": "Pro-government perspective (opinion) — not news reporting",
  "analysis": {
    "summary": "...",
    "category": "prices_inflation",
    "tone_toward_government": "negative",
    "facts": ["..."],
    "stated_causes": ["..."],
    "event_date_hint": null
  },
  "technique": {
    "key": "external_attribution",
    "description": "Attribute the problem to genuine external factors ...",
    "secondary": ["juxtaposition"]
  },
  "output": {
    "headline": "...",
    "perspective": "...",
    "key_points": ["..."],
    "claims_needing_citation": ["..."],
    "honest_limit": null
  },
  "fact_guard": {
    "verdict": "revised",
    "issues": [
      { "type": "false_causation", "text": "...", "explanation": "..." }
    ]
  },
  "draft": { "...": "unedited output of the Frame stage" }
}
```

**Status codes**

| Code | Meaning |
|------|---------|
| `200` | Success |
| `422` | Neither headline nor content was provided, or a field is too long |
| `502` | The LLM call or pipeline failed |
| `503` | `OPENAI_API_KEY` is not set on the server |

---

## Testing

The tests replace the LLM with a deterministic stub, so they need no API key and no network access.

```bash
pip install pytest httpx
pytest
```

The suite checks that:

- the fact-guard's revised output replaces the original draft,
- unknown technique keys are filtered out,
- empty input is rejected,
- the `/`, `/health` and `/api/frame` endpoints behave as expected.

---

## Responsible Use

Framing Lens is built for **academic research and media-literacy education**. It is not meant for producing propaganda or disinformation.

- Every output is explicitly labelled as **opinion**.
- The prompts forbid inventing facts, statistics, quotes or sources.
- A separate audit stage removes false causation and impossible chronology.
- When no honest favourable angle exists, the system says so in `honest_limit` instead of forcing one.
- General-knowledge claims are listed under `claims_needing_citation` so readers can verify them.

**Limitations:** LLMs can still make mistakes, and the fact-guard is itself an LLM, not a source of ground truth. Verify every claim independently before you cite or share any output.

---

## Roadmap

- [ ] **Spin detector:** classify real news articles by framing technique and compare outlets.
- [ ] **Human evaluation:** have annotators rate outputs for persuasiveness against factual accuracy.
- [ ] **Source retrieval:** cite official sources (PIB, RBI, MoSPI) for the "claims to verify".

---

<p align="center"><i>Built as an academic project on political framing and media literacy.</i></p>
