import json

from evals.models import EvalCase, EvalResult


def score_response(
    case: EvalCase,
    answer: str,
    citations: list[str],
    latency_ms: float = 0.0,
    estimated_cost_usd: float = 0.0,
) -> EvalResult:
    fact_hits = sum(1 for fact in case.expected_facts if fact.lower() in answer.lower())
    citation_hits = sum(1 for citation in case.required_citations if citation in citations)

    relevance = fact_hits / max(len(case.expected_facts), 1)
    citation_score = (
        citation_hits / len(case.required_citations) if case.required_citations else 1.0
    )
    groundedness = min(relevance, citation_score) if case.required_citations else relevance
    json_validity = _score_json_validity(answer) if case.expect_json else 1.0
    notes = _build_notes(case, relevance, citation_score, json_validity)

    return EvalResult(
        case_id=case.id,
        passed=relevance >= 0.8 and citation_score >= 0.8 and json_validity >= 1.0,
        relevance_score=relevance,
        groundedness_score=groundedness,
        citation_score=citation_score,
        json_validity_score=json_validity,
        latency_ms=latency_ms,
        estimated_cost_usd=estimated_cost_usd,
        notes="; ".join(notes),
    )


def _score_json_validity(answer: str) -> float:
    try:
        json.loads(answer)
    except json.JSONDecodeError:
        return 0.0
    return 1.0


def _build_notes(
    case: EvalCase,
    relevance: float,
    citation_score: float,
    json_validity: float,
) -> list[str]:
    notes: list[str] = []
    if relevance < 0.8:
        notes.append("Expected facts were missing from the answer")
    if case.required_citations and citation_score < 0.8:
        notes.append("Required citations were missing")
    if json_validity < 1.0:
        notes.append("Answer was not valid JSON")
    return notes
