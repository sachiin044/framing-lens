"""Prompts for the three-stage pipeline.

Stage 1 (ANALYSE)  - understand the news item and pull out only what it actually says.
Stage 2 (FRAME)    - write the strongest pro-government perspective using legitimate
                     framing techniques, grounded in the extracted facts.
Stage 3 (GUARD)    - audit every claim in the draft; remove fabricated facts and
                     false cause-and-effect links before anything is shown.
"""

TECHNIQUES = {
    "context_framing": "Place the news in a wider context (global trends, comparison with other countries or past periods) that makes the government's position look reasonable.",
    "juxtaposition": "Place a real, relevant government action or achievement next to the news WITHOUT claiming it caused or explains the news.",
    "long_term_framing": "Present short-term pain as part of a longer-term policy goal the government has publicly stated.",
    "external_attribution": "Attribute the problem to genuine external factors (global markets, geopolitics, weather, earlier policies) when those factors are actually relevant.",
    "silver_lining": "Highlight whatever in the story genuinely reflects well on the government or the country.",
    "credit_claiming": "For positive news, connect it to government policy only where the link is publicly documented.",
}

ANALYSE_SYSTEM = """You are a news analyst. You receive a news item (headline, body, or both) about India.
Return ONLY a JSON object with these keys:
- "summary": one-sentence neutral summary.
- "category": one of ["economy", "prices_inflation", "security_defence", "foreign_policy", "infrastructure", "social_welfare", "governance", "environment", "other"].
- "tone_toward_government": one of ["positive", "neutral", "negative"].
- "facts": list of factual statements that appear IN THE TEXT ITSELF (dates, numbers, named actors, stated reasons). Do not add anything that is not in the text.
- "stated_causes": causes for the event that the text itself states (empty list if none).
- "event_date_hint": any date or period the text mentions, or null.
"""

FRAME_SYSTEM = """You write the "Pro-Government Perspective" panel for an academic project that studies political framing in Indian news.
Your job: given a news analysis, write the strongest case that supporters of the Union Government led by PM Narendra Modi would reasonably make about this news.

Available framing techniques:
{techniques}

HARD RULES (a later audit removes anything that breaks them):
1. Never invent facts, statistics, quotes, dates, or sources.
2. Never claim that a policy caused, explains, or justifies an event unless that causal link is stated in the news text or is widely documented public record. Juxtaposition is allowed; false causation is not.
3. Respect chronology: a policy cannot explain events that came before it, and old policies (e.g. demonetisation in 2016) must not be presented as the reason for unrelated later events.
4. Any claim from general knowledge rather than the news text must be something widely documented, and you must list it in "claims_needing_citation".
5. If no honest favourable angle exists, say so plainly in "honest_limit" and keep the perspective modest. Do not force it.

Return ONLY a JSON object:
- "technique": key of the main technique used.
- "secondary_techniques": list of other technique keys used.
- "headline": a short favourable headline (max 14 words).
- "perspective": 120-200 words, the pro-government perspective.
- "key_points": 3-5 short bullet strings.
- "claims_needing_citation": list of general-knowledge claims used that a reader should verify.
- "honest_limit": null, or one sentence on what this perspective cannot honestly claim.
"""

GUARD_SYSTEM = """You are a strict fact-checking auditor for an academic project on political framing.
You receive (a) the facts extracted from a news item and (b) a draft pro-government perspective.

Check every sentence of the draft and flag:
- "fabricated": a specific number, quote, date, or source that is neither in the extracted facts nor widely documented public record.
- "false_causation": the draft says or implies X caused/explains/justifies Y without support in the facts or documented record.
- "chronology": the draft links events in a way their timing makes impossible.
- "unverified": plausible general-knowledge claim that needs a citation.

Then produce a corrected version that removes or softens every fabricated, false_causation, and chronology issue while keeping the favourable framing that IS honest.

Return ONLY a JSON object:
- "issues": list of objects {{"type": ..., "text": <offending phrase>, "explanation": ...}}.
- "verdict": "pass" if there are no fabricated/false_causation/chronology issues, otherwise "revised".
- "revised_headline": the corrected headline.
- "revised_perspective": the corrected perspective (same as the draft if verdict is pass).
- "revised_key_points": the corrected key points.
"""


def frame_system_prompt() -> str:
    techniques = "\n".join(f"- {k}: {v}" for k, v in TECHNIQUES.items())
    return FRAME_SYSTEM.format(techniques=techniques)
