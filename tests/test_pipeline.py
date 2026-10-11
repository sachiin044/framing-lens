"""Tests with a stubbed LLM so they run without an API key."""
from fastapi.testclient import TestClient

from app import main
from app.pipeline import run_pipeline


def fake_llm(system: str, user: str):
    if system.startswith("You are a news analyst"):
        return {
            "summary": "Petrol prices rose by Rs 2 per litre.",
            "category": "prices_inflation",
            "tone_toward_government": "negative",
            "facts": ["Petrol price rose by Rs 2 per litre"],
            "stated_causes": ["Higher global crude prices"],
            "event_date_hint": None,
        }
    if "Pro-Government Perspective" in system:
        return {
            "technique": "external_attribution",
            "secondary_techniques": ["juxtaposition", "made_up_key"],
            "headline": "Demonetisation explains fuel price rise",
            "perspective": "Because of demonetisation, prices rose.",
            "key_points": ["a", "b", "c"],
            "claims_needing_citation": [],
            "honest_limit": None,
        }
    return {
        "issues": [{"type": "false_causation", "text": "Because of demonetisation",
                    "explanation": "No link between 2016 demonetisation and this price rise."}],
        "verdict": "revised",
        "revised_headline": "Global crude drives modest fuel price rise",
        "revised_perspective": "The rise tracks global crude prices, as the report states.",
        "revised_key_points": ["Global crude is the stated cause"],
    }


def test_guard_output_replaces_draft():
    r = run_pipeline("Petrol prices rise", None, fake_llm)
    assert r["output"]["headline"] == "Global crude drives modest fuel price rise"
    assert "demonetisation" not in r["output"]["perspective"].lower()
    assert r["fact_guard"]["verdict"] == "revised"
    assert r["technique"]["secondary"] == ["juxtaposition"]
    assert "opinion" in r["label"]


def test_requires_input():
    import pytest
    with pytest.raises(ValueError):
        run_pipeline("  ", "", fake_llm)


def test_api(monkeypatch):
    monkeypatch.setattr(main, "get_llm", lambda: fake_llm)
    c = TestClient(main.app)
    assert c.get("/health").json()["status"] == "ok"
    assert c.get("/").status_code == 200
    assert c.post("/api/frame", json={}).status_code == 422
    r = c.post("/api/frame", json={"headline": "Petrol prices rise"})
    assert r.status_code == 200 and r.json()["fact_guard"]["issues"]
