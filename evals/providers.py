import time
import re
from typing import Protocol

from evals.models import EvalCase, ModelResponse
from evals.runner_utils import estimate_cost


class EvalProvider(Protocol):
    name: str

    def generate(self, case: EvalCase) -> ModelResponse:
        pass


class DatasetCandidateProvider:
    name = "dataset-candidate"

    def generate(self, case: EvalCase) -> ModelResponse:
        start = time.perf_counter()
        answer = case.candidate_answer or ""
        latency_ms = (time.perf_counter() - start) * 1000
        return ModelResponse(
            answer=answer,
            citations=case.candidate_citations,
            latency_ms=latency_ms,
            estimated_cost_usd=estimate_cost(answer),
        )


class EchoProvider:
    name = "echo"

    def generate(self, case: EvalCase) -> ModelResponse:
        start = time.perf_counter()
        answer = f"Echo response for: {case.question}"
        latency_ms = (time.perf_counter() - start) * 1000
        return ModelResponse(
            answer=answer,
            latency_ms=latency_ms,
            estimated_cost_usd=estimate_cost(answer),
        )


class OpenAIResponsesProvider:
    name = "openai"

    def __init__(self, model: str = "gpt-4.1", client: object | None = None) -> None:
        self.model = model
        self._client = client

    def generate(self, case: EvalCase) -> ModelResponse:
        start = time.perf_counter()
        response = self.client.responses.create(
            model=self.model,
            input=build_openai_prompt(case),
        )
        answer = response.output_text
        latency_ms = (time.perf_counter() - start) * 1000
        return ModelResponse(
            answer=answer,
            citations=extract_inline_citations(answer),
            latency_ms=latency_ms,
            estimated_cost_usd=estimate_cost(answer),
        )

    @property
    def client(self) -> object:
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise RuntimeError(
                    "The OpenAI provider requires the optional dependency: "
                    "pip install -e .[openai]"
                ) from exc
            self._client = OpenAI()
        return self._client


def build_openai_prompt(case: EvalCase) -> str:
    context = "\n\n".join(
        f"[{document.document_id}]\n{document.text}" for document in case.context
    )
    output_instruction = (
        "Return valid JSON only." if case.expect_json else "Answer in concise plain text."
    )
    citation_instruction = (
        "When using context, cite document IDs inline in square brackets, for example [doc-1]."
    )
    context_section = context or "No retrieval context was provided."
    return (
        f"{output_instruction}\n"
        f"{citation_instruction}\n\n"
        f"Question:\n{case.question}\n\n"
        f"Context:\n{context_section}"
    )


def extract_inline_citations(answer: str) -> list[str]:
    return sorted(set(re.findall(r"\[([A-Za-z0-9_.:-]+)\]", answer)))


def get_provider(name: str, model: str | None = None) -> EvalProvider:
    providers: dict[str, EvalProvider] = {
        DatasetCandidateProvider.name: DatasetCandidateProvider(),
        EchoProvider.name: EchoProvider(),
        OpenAIResponsesProvider.name: OpenAIResponsesProvider(model=model or "gpt-4.1"),
    }
    try:
        return providers[name]
    except KeyError as exc:
        available = ", ".join(sorted(providers))
        raise ValueError(f"Unknown provider '{name}'. Available providers: {available}") from exc
