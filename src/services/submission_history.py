"""Submission history loading and summarization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_submission_history(path: str | Path) -> dict[str, Any]:
    """Load submission history from disk."""
    history_path = Path(path)
    if not history_path.exists():
        return {"submissions": []}
    try:
        data = json.loads(history_path.read_text())
    except json.JSONDecodeError:
        return {"submissions": []}
    if not isinstance(data, dict):
        return {"submissions": []}
    data.setdefault("submissions", [])
    return data


def summarize_submissions(submissions: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize submission history for UI rendering."""
    rows: list[dict[str, Any]] = []
    mse_scores: list[float] = []
    for idx, sub in enumerate(submissions, 1):
        ts = str(sub.get("timestamp", ""))[:19].replace("T", " ")
        set_type = sub.get("set_type", "")
        mse = sub.get("mse_score")
        num = sub.get("num_predictions", 0)
        config = sub.get("config", {}) if isinstance(sub.get("config"), dict) else {}
        rows.append(
            {
                "#": idx,
                "Timestamp": ts,
                "Set": set_type,
                "MSE": mse,
                "Preds": num,
                "Turns": config.get("turns"),
                "Parallel": config.get("parallel"),
            }
        )
        if isinstance(mse, (int, float)):
            mse_scores.append(float(mse))

    stats = None
    if mse_scores:
        best = min(mse_scores)
        worst = max(mse_scores)
        avg = sum(mse_scores) / len(mse_scores)
        trend = mse_scores[-1] - mse_scores[0]
        stats = {
            "best": best,
            "worst": worst,
            "avg": avg,
            "trend": trend,
        }

    best_sub = None
    if submissions:
        valid = [sub for sub in submissions if isinstance(sub.get("mse_score"), (int, float))]
        if valid:
            best_sub = min(valid, key=lambda x: x["mse_score"])

    return {"rows": rows, "stats": stats, "best": best_sub}
