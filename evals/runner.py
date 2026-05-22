import json
import uuid
from pathlib import Path

import typer

from evals.models import EvalCase, EvalResult, EvalRunReport, EvalSummary
from evals.providers import EvalProvider, get_provider
from evals.runner_utils import average, percentile
from evals.scorers import score_response
from evals.storage import list_run_summaries, save_run_report

app = typer.Typer()


@app.command()
def run(
    dataset_path: Path,
    report_path: Path | None = typer.Option(
        None,
        "--report-path",
        help="Write a JSON report with summary metrics and per-case results.",
    ),
    min_pass_rate: float = typer.Option(
        0.8,
        "--min-pass-rate",
        help="Quality gate threshold for the case pass rate.",
    ),
    min_average_groundedness: float = typer.Option(
        0.8,
        "--min-average-groundedness",
        help="Quality gate threshold for average groundedness.",
    ),
    provider_name: str = typer.Option(
        "dataset-candidate",
        "--provider",
        help="Answer provider to evaluate. Use dataset-candidate for local JSONL answers.",
    ),
    model: str | None = typer.Option(
        None,
        "--model",
        help="Provider model name. Used by provider implementations such as openai.",
    ),
    history_db: Path | None = typer.Option(
        None,
        "--history-db",
        help="Persist the run summary and full report JSON to a SQLite database.",
    ),
) -> None:
    provider = get_provider(provider_name, model)
    report = run_dataset(dataset_path, min_pass_rate, min_average_groundedness, provider)

    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

    if history_db:
        save_run_report(history_db, report)

    typer.echo(report.model_dump_json(indent=2))

    if not report.summary.quality_gate_passed:
        raise typer.Exit(code=1)


@app.command()
def history(
    history_db: Path = typer.Argument(..., help="SQLite database created by --history-db."),
    limit: int = typer.Option(10, "--limit", help="Number of recent runs to show."),
) -> None:
    typer.echo(json.dumps(list_run_summaries(history_db, limit), indent=2))


def run_dataset(
    dataset_path: Path,
    min_pass_rate: float = 0.8,
    min_average_groundedness: float = 0.8,
    provider: EvalProvider | None = None,
) -> EvalRunReport:
    cases = load_cases(dataset_path)
    provider = provider or get_provider("dataset-candidate")
    results = []

    for case in cases:
        response = provider.generate(case)
        results.append(
            score_response(
                case,
                response.answer,
                response.citations,
                latency_ms=response.latency_ms,
                estimated_cost_usd=response.estimated_cost_usd,
            )
        )

    summary = summarize(results, min_pass_rate, min_average_groundedness)
    return EvalRunReport(
        run_id=str(uuid.uuid4()),
        dataset_path=str(dataset_path),
        summary=summary,
        results=results,
    )


def load_cases(dataset_path: Path) -> list[EvalCase]:
    cases: list[EvalCase] = []
    for line_number, line in enumerate(dataset_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            cases.append(EvalCase.model_validate_json(line))
        except ValueError as exc:
            raise typer.BadParameter(f"Invalid JSONL at line {line_number}: {exc}") from exc
    return cases


def summarize(
    results: list[EvalResult],
    min_pass_rate: float,
    min_average_groundedness: float,
) -> EvalSummary:
    total_cases = len(results)
    passed_cases = sum(1 for result in results if result.passed)
    pass_rate = passed_cases / total_cases if total_cases else 0.0
    average_groundedness = average([result.groundedness_score for result in results])

    return EvalSummary(
        total_cases=total_cases,
        passed_cases=passed_cases,
        pass_rate=pass_rate,
        average_relevance=average([result.relevance_score for result in results]),
        average_groundedness=average_groundedness,
        average_citation=average([result.citation_score for result in results]),
        average_json_validity=average([result.json_validity_score for result in results]),
        total_estimated_cost_usd=sum(result.estimated_cost_usd for result in results),
        p95_latency_ms=percentile([result.latency_ms for result in results], 0.95),
        quality_gate_passed=pass_rate >= min_pass_rate
        and average_groundedness >= min_average_groundedness,
    )


if __name__ == "__main__":
    app()
