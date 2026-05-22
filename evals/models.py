from datetime import UTC, datetime

from pydantic import BaseModel, Field


class EvalCase(BaseModel):
    id: str
    question: str
    context: list["ContextDocument"] = Field(default_factory=list)
    expected_facts: list[str] = Field(default_factory=list)
    required_citations: list[str] = Field(default_factory=list)
    candidate_answer: str | None = None
    candidate_citations: list[str] = Field(default_factory=list)
    expect_json: bool = False
    metadata: dict[str, str] = Field(default_factory=dict)


class ContextDocument(BaseModel):
    document_id: str
    text: str


class EvalResult(BaseModel):
    case_id: str
    passed: bool
    relevance_score: float
    groundedness_score: float
    citation_score: float
    json_validity_score: float = 1.0
    latency_ms: float = 0.0
    estimated_cost_usd: float = 0.0
    notes: str = ""


class ModelResponse(BaseModel):
    answer: str
    citations: list[str] = Field(default_factory=list)
    latency_ms: float = 0.0
    estimated_cost_usd: float = 0.0


class EvalSummary(BaseModel):
    total_cases: int
    passed_cases: int
    pass_rate: float
    average_relevance: float
    average_groundedness: float
    average_citation: float
    average_json_validity: float
    total_estimated_cost_usd: float
    p95_latency_ms: float
    quality_gate_passed: bool


class EvalRunReport(BaseModel):
    run_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    dataset_path: str
    summary: EvalSummary
    results: list[EvalResult]
