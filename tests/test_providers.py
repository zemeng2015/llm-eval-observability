from evals.models import EvalCase
from evals.providers import (
    DatasetCandidateProvider,
    EchoProvider,
    OpenAIResponsesProvider,
    build_openai_prompt,
    extract_inline_citations,
    get_provider,
)


def test_dataset_candidate_provider_reads_answer_from_case() -> None:
    case = EvalCase(
        id="case-001",
        question="What changed?",
        candidate_answer="Risk improved.",
        candidate_citations=["doc-1"],
    )

    response = DatasetCandidateProvider().generate(case)

    assert response.answer == "Risk improved."
    assert response.citations == ["doc-1"]
    assert response.estimated_cost_usd > 0


def test_get_provider_returns_echo_provider() -> None:
    provider = get_provider("echo")

    assert isinstance(provider, EchoProvider)


def test_openai_prompt_includes_question_and_context() -> None:
    case = EvalCase(
        id="case-002",
        question="What changed?",
        context=[{"document_id": "doc-1", "text": "Risk improved in Q2."}],
    )

    prompt = build_openai_prompt(case)

    assert "What changed?" in prompt
    assert "[doc-1]" in prompt
    assert "Risk improved in Q2." in prompt


def test_extract_inline_citations_deduplicates_ids() -> None:
    citations = extract_inline_citations("Risk improved [doc-1]. See also [doc-1] and [doc:2].")

    assert citations == ["doc-1", "doc:2"]


def test_openai_provider_uses_responses_api_client() -> None:
    class FakeResponse:
        output_text = "Risk improved [doc-1]."

    class FakeResponses:
        def create(self, model: str, input: str) -> FakeResponse:
            assert model == "test-model"
            assert "What changed?" in input
            return FakeResponse()

    class FakeClient:
        responses = FakeResponses()

    case = EvalCase(
        id="case-003",
        question="What changed?",
        context=[{"document_id": "doc-1", "text": "Risk improved in Q2."}],
    )

    response = OpenAIResponsesProvider(model="test-model", client=FakeClient()).generate(case)

    assert response.answer == "Risk improved [doc-1]."
    assert response.citations == ["doc-1"]
