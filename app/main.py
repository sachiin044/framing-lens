"""FastAPI entry point."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .pipeline import openai_llm, run_pipeline

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Framing Lens", version="1.0.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

_llm = None


def get_llm():
    global _llm
    if _llm is None:
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(503, "OPENAI_API_KEY is not set on the server.")
        _llm = openai_llm()
    return _llm


class NewsIn(BaseModel):
    headline: str | None = Field(default=None, max_length=500)
    content: str | None = Field(default=None, max_length=12000)


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "llm_configured": bool(os.getenv("OPENAI_API_KEY"))}


@app.post("/api/frame")
def frame(news: NewsIn):
    if not (news.headline or "").strip() and not (news.content or "").strip():
        raise HTTPException(422, "Provide a headline, content, or both.")
    try:
        return run_pipeline(news.headline, news.content, get_llm())
    except HTTPException:
        raise
    except Exception as exc:  # surface LLM/API errors to the UI
        raise HTTPException(502, f"Pipeline failed: {exc}") from exc
