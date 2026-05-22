from pathlib import Path

from evals.runner import run_dataset
from evals.storage import list_run_summaries, save_run_report


def test_save_run_report_persists_summary(tmp_path: Path) -> None:
    dataset_path = tmp_path / "cases.jsonl"
    dataset_path.write_text(
        '{"id":"case-001","question":"What changed?",'
        '"expected_facts":["risk improved"],"required_citations":["doc-1"],'
        '"candidate_answer":"Risk improved.","candidate_citations":["doc-1"]}',
        encoding="utf-8",
    )
    report = run_dataset(dataset_path)
    db_path = tmp_path / "history.db"

    save_run_report(db_path, report)
    summaries = list_run_summaries(db_path)

    assert len(summaries) == 1
    assert summaries[0]["run_id"] == report.run_id
    assert summaries[0]["passed_cases"] == 1
    assert summaries[0]["quality_gate_passed"] == 1
