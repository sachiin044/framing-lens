"""Three-stage framing pipeline: analyse -> frame -> guard."""
from __future__ import annotations

import json
import os
from typing import Any, Callable, Protocol

from .prompts import ANALYSE_SYSTEM, GUARD_SYSTEM, TECHNIQUES, frame_system_prompt

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


class LLM(Protocol):
    def __call__(self, system: str, user: str) -> dict[str, Any]: ...


def openai_llm(model: str | None = None) -> LLM:
    """Return a callable that sends system+user prompts to OpenAI and parses JSON."""
    from openai import OpenAI

    client = OpenAI()  # reads OPENAI_API_KEY from the environment
    model_name = model or DEFAULT_MODEL

    def call(system: str, user: str) -> dict[str, Any]:
        resp = client.chat.completions.create(
            model=model_name,
            temperature=0.4,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return json.loads(resp.choices[0].message.content or "{}")

    return call


def build_news_text(headline: str | None, content: str | None) -> str:
    parts = []
    if headline and headline.strip():
        parts.append(f"HEADLINE: {headline.strip()}")
    if content and content.strip():
        parts.append(f"CONTENT: {content.strip()}")
    if not parts:
        raise ValueError("Provide a headline, content, or both.")
    return "\n\n".join(parts)


def run_pipeline(headline: str | None, content: str | None, llm: LLM) -> dict[str, Any]:
    news = build_news_text(headline, content)

    analysis = llm(ANALYSE_SYSTEM, news)

    frame_input = (
        f"NEWS ITEM:\n{news}\n\nANALYSIS:\n{json.dumps(analysis, ensure_ascii=False, indent=2)}"
    )
    draft = llm(frame_system_prompt(), frame_input)

    guard_input = (
        f"EXTRACTED FACTS:\n{json.dumps(analysis.get('facts', []), ensure_ascii=False)}\n"
        f"STATED CAUSES:\n{json.dumps(analysis.get('stated_causes', []), ensure_ascii=False)}\n\n"
        f"DRAFT:\n{json.dumps(draft, ensure_ascii=False, indent=2)}"
    )
    audit = llm(GUARD_SYSTEM, guard_input)

    technique = draft.get("technique")
    return {
        "label": "Pro-government perspective (opinion) — not news reporting",
        "analysis": analysis,
        "technique": {
            "key": technique,
            "description": TECHNIQUES.get(technique, "Unrecognised technique"),
            "secondary": [t for t in draft.get("secondary_techniques", []) if t in TECHNIQUES],
        },
        "output": {
            "headline": audit.get("revised_headline") or draft.get("headline"),
            "perspective": audit.get("revised_perspective") or draft.get("perspective"),
            "key_points": audit.get("revised_key_points") or draft.get("key_points", []),
            "claims_needing_citation": draft.get("claims_needing_citation", []),
            "honest_limit": draft.get("honest_limit"),
        },
        "fact_guard": {
            "verdict": audit.get("verdict", "unknown"),
            "issues": audit.get("issues", []),
        },
        "draft": draft,
    }
