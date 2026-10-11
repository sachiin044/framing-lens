# Framing Lens

An academic project on political framing in Indian news. Given a news headline and/or article, it:

1. **Analyses** the item: neutral summary, category, tone toward the government, and the facts and causes the text itself states.
2. **Frames** it: writes the strongest pro-government perspective supporters would make, using a named, legitimate framing technique (context framing, juxtaposition, long-term framing, external attribution, silver lining, credit claiming).
3. **Guards** it: a separate audit pass flags fabricated facts, false cause-and-effect links and impossible chronology (e.g. blaming a 2026 event on 2016 demonetisation), then rewrites the draft without them.

Every output is labelled as opinion and shows the technique used, claims to verify, and the issues the fact-guard removed.

## Architecture

```
Browser (static/index.html)
   │  POST /api/frame {headline, content}
   ▼
FastAPI (app/main.py)
   │
   ▼
Pipeline (app/pipeline.py)
   ├─ 1. ANALYSE  → facts, stated causes, category, tone
   ├─ 2. FRAME    → technique + pro-government perspective (draft)
   └─ 3. GUARD    → issues list + revised perspective
   │
   ▼
OpenAI Chat Completions (JSON mode), model from OPENAI_MODEL
```

## Run locally

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
uvicorn app.main:app --reload
# open http://localhost:8000
```

Tests (no API key needed): `pip install pytest httpx && pytest`

## Deploy on Render

1. Push this folder to a GitHub repo.
2. In Render: **New → Blueprint**, pick the repo (uses `render.yaml`), or create a Python web service with
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. In the service's **Environment** tab, add `OPENAI_API_KEY`. Never commit the key.

## Ideas for extending the project

- Spin detector: classify real news articles by framing technique and compare outlets.
- Evaluation: have annotators rate outputs for persuasiveness vs. factual accuracy.
- Add retrieval from official sources (PIB, RBI, MoSPI) to cite the "claims to verify".
