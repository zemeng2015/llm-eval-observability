# LLM Evaluation & Observability Platform

Evaluation and monitoring platform for RAG and agent workflows.

## Why This Project

AI engineering interviews increasingly test whether you can make LLM systems reliable, measurable, and maintainable. This project focuses on evals, regression testing, trace collection, latency, cost, and quality gates.

## Target Resume Bullet

Built an LLM evaluation platform with regression datasets, automated scoring, prompt/version tracking, and CI quality gates for RAG and agent workflows.

## Core Capabilities

- Store golden test cases for RAG and agent workflows.
- Run local prompt/model/version comparisons from JSONL datasets.
- Score answer relevance, citation correctness, groundedness, JSON validity, latency, and cost.
- Export JSON reports for CI and dashboards.
- Track failures by prompt version and dataset.

## Current Implementation

This first version is intentionally local-first: eval cases include candidate answers and
citations, so the reliability layer can be developed without depending on a live LLM provider.

- JSONL eval case schema with expected facts, required citations, structured-output checks,
  retrieval context, and metadata such as workflow and prompt version.
- Scoring for relevance, citation correctness, groundedness, JSON validity, latency, and
  estimated cost.
- CLI runner that emits a full JSON report with per-case results and aggregate metrics.
- Quality gate that exits non-zero when pass rate or groundedness falls below threshold.
- Provider adapter interface with local `dataset-candidate` and `echo` providers.
- Optional OpenAI Responses API provider for real model evals.
- SQLite run history for tracking pass rate and groundedness over time.
- Unit tests for scorer behavior and runner summaries.

## Suggested Stack

- Backend: FastAPI, Pydantic
- Storage: SQLite locally, Postgres later
- Eval runner: pytest-compatible CLI
- Observability: OpenTelemetry-style traces, JSONL run logs
- Dashboard later: React or Streamlit

## Milestones

1. Define eval case schema and JSONL datasets.
2. Build local eval runner.
3. Add scoring modules.
4. Add run history and report export.
5. Add CI quality gate.

## Local Development

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -e ".[dev]"
python -m evals.runner run datasets/sample.jsonl --report-path runs/sample-report.json
python -m pytest
python -m ruff check .
```

Persist run history to SQLite:

```bash
python -m evals.runner run datasets/sample.jsonl \
  --report-path runs/sample-report.json \
  --history-db runs/history.db
python -m evals.runner history runs/history.db
```

Evaluate with a different local provider:

```bash
python -m evals.runner run datasets/sample.jsonl --provider echo
```

Evaluate a real OpenAI model:

```bash
pip install -e ".[openai]"
$env:OPENAI_API_KEY="your_api_key"
python -m evals.runner run datasets/sample.jsonl --provider openai --model gpt-4.1
```

The OpenAI provider uses the Responses API and extracts inline citations from model answers
such as `[sample-report]`.

## Example Report Summary

The sample dataset currently passes the quality gate:

```json
{
  "total_cases": 2,
  "passed_cases": 2,
  "pass_rate": 1.0,
  "average_groundedness": 1.0,
  "quality_gate_passed": true
}
```

## Next Milestones

1. Add provider adapters for OpenAI and Bedrock.
2. Add prompt/model/version comparison reports.
3. Add GitHub Actions quality gate.
4. Add a lightweight FastAPI endpoint for run history.
5. Connect this eval runner to the mortgage RAG copilot.
