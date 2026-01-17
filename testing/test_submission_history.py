"""Tests for submission history helpers."""

from src.services.submission_history import load_submission_history, summarize_submissions


def test_load_submission_history_missing_returns_empty(tmp_path):
    path = tmp_path / "submission_history.json"

    data = load_submission_history(path)

    assert data == {"submissions": []}


def test_summarize_submissions_returns_stats_and_rows():
    submissions = [
        {
            "timestamp": "2026-01-01T10:00:00",
            "set_type": "mini_dev",
            "mse_score": 0.9,
            "num_predictions": 10,
            "config": {"turns": 8, "parallel": 2},
        },
        {
            "timestamp": "2026-01-02T10:00:00",
            "set_type": "mini_dev",
            "mse_score": 0.7,
            "num_predictions": 10,
            "config": {"turns": 8, "parallel": 2},
        },
    ]

    summary = summarize_submissions(submissions)

    assert len(summary["rows"]) == 2
    assert summary["stats"]["best"] == 0.7
    assert summary["stats"]["worst"] == 0.9
    assert round(summary["stats"]["trend"], 4) == -0.2
    assert summary["best"]["mse_score"] == 0.7
