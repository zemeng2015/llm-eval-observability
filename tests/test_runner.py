from pathlib import Path

from evals.runner import run_dataset


def test_run_dataset_builds_summary(tmp_path: Path) -> None:
    dataset_path = tmp_path / "cases.jsonl"
    dataset_path.write_text(
        "\n".join(
            [
                '{"id":"case-001","question":"What changed?",'
                '"expected_facts":["risk improved"],"required_citations":["doc-1"],'
                '"candidate_answer":"Risk improved in Q2.","candidate_citations":["doc-1"]}',
                '{"id":"case-002","question":"Return JSON","expected_facts":["risk"],'
                '"candidate_answer":"{\\"risk\\":\\"stable\\"}","expect_json":true}',
            ]
        ),
        encoding="utf-8",
    )

    report = run_dataset(dataset_path)

    assert report.summary.total_cases == 2
    assert report.summary.passed_cases == 2
    assert report.summary.quality_gate_passed


def test_run_dataset_quality_gate_fails_when_answer_is_missing(tmp_path: Path) -> None:
    dataset_path = tmp_path / "cases.jsonl"
    dataset_path.write_text(
        '{"id":"case-001","question":"What changed?",'
        '"expected_facts":["risk improved"],"required_citations":["doc-1"]}',
        encoding="utf-8",
    )

    report = run_dataset(dataset_path)

    assert report.summary.passed_cases == 0
    assert not report.summary.quality_gate_passed
