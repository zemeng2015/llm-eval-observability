from evals.models import EvalCase
from evals.scorers import score_response


def test_score_response_passes_when_facts_and_citations_match() -> None:
    case = EvalCase(
        id="case-001",
        question="What changed?",
        expected_facts=["delinquency improved"],
        required_citations=["doc-1"],
    )

    result = score_response(case, "Delinquency improved in Q2.", ["doc-1"])

    assert result.passed


def test_score_response_fails_when_required_citation_is_missing() -> None:
    case = EvalCase(
        id="case-002",
        question="What changed?",
        expected_facts=["delinquency improved"],
        required_citations=["doc-1"],
    )

    result = score_response(case, "Delinquency improved in Q2.", [])

    assert not result.passed
    assert result.citation_score == 0.0
    assert "Required citations were missing" in result.notes


def test_score_response_validates_json_when_expected() -> None:
    case = EvalCase(
        id="case-003",
        question="Return JSON",
        expected_facts=["risk"],
        expect_json=True,
    )

    result = score_response(case, "risk: stable", [])

    assert not result.passed
    assert result.json_validity_score == 0.0
    assert "Answer was not valid JSON" in result.notes
