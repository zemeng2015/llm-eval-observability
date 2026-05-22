import sqlite3
from pathlib import Path

from evals.models import EvalRunReport


def save_run_report(db_path: Path, report: EvalRunReport) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        initialize_db(connection)
        connection.execute(
            """
            INSERT INTO eval_runs (
                run_id,
                created_at,
                dataset_path,
                total_cases,
                passed_cases,
                pass_rate,
                average_groundedness,
                quality_gate_passed,
                report_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report.run_id,
                report.created_at.isoformat(),
                report.dataset_path,
                report.summary.total_cases,
                report.summary.passed_cases,
                report.summary.pass_rate,
                report.summary.average_groundedness,
                int(report.summary.quality_gate_passed),
                report.model_dump_json(),
            ),
        )


def list_run_summaries(db_path: Path, limit: int = 10) -> list[dict[str, object]]:
    if not db_path.exists():
        return []
    with sqlite3.connect(db_path) as connection:
        initialize_db(connection)
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT
                run_id,
                created_at,
                dataset_path,
                total_cases,
                passed_cases,
                pass_rate,
                average_groundedness,
                quality_gate_passed
            FROM eval_runs
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def initialize_db(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS eval_runs (
            run_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            dataset_path TEXT NOT NULL,
            total_cases INTEGER NOT NULL,
            passed_cases INTEGER NOT NULL,
            pass_rate REAL NOT NULL,
            average_groundedness REAL NOT NULL,
            quality_gate_passed INTEGER NOT NULL,
            report_json TEXT NOT NULL
        )
        """
    )
