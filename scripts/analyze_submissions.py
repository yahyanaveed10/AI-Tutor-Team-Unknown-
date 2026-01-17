#!/usr/bin/env python3
"""Analyze submission history to track MSE trends and suggest improvements."""

import json
from pathlib import Path


def analyze_submissions():
    history_path = Path("data/submission_history.json")
    
    if not history_path.exists():
        print("No submission history found. Run with --submit first.")
        return
    
    history = json.loads(history_path.read_text())
    submissions = history.get("submissions", [])
    
    if not submissions:
        print("No submissions recorded yet.")
        return
    
    print(f"\n{'='*60}")
    print(f"SUBMISSION HISTORY ANALYSIS ({len(submissions)} submissions)")
    print(f"{'='*60}\n")
    
    # Table header
    print(f"{'#':<4} {'Timestamp':<20} {'Set':<10} {'MSE':<8} {'Preds':<6}")
    print("-" * 60)
    
    mse_scores = []
    for i, sub in enumerate(submissions, 1):
        ts = sub["timestamp"][:16].replace("T", " ")
        set_type = sub["set_type"]
        mse = sub["mse_score"]
        num = sub["num_predictions"]
        
        mse_scores.append(mse)
        
        # Color code MSE (terminal colors)
        if mse <= 0.5:
            mse_str = f"\033[92m{mse:.4f}\033[0m"  # Green
        elif mse <= 1.0:
            mse_str = f"\033[93m{mse:.4f}\033[0m"  # Yellow
        else:
            mse_str = f"\033[91m{mse:.4f}\033[0m"  # Red
        
        print(f"{i:<4} {ts:<20} {set_type:<10} {mse_str:<17} {num:<6}")
    
    print("-" * 60)
    
    # Stats
    if len(mse_scores) >= 2:
        best = min(mse_scores)
        worst = max(mse_scores)
        avg = sum(mse_scores) / len(mse_scores)
        trend = mse_scores[-1] - mse_scores[0]
        
        print(f"\nStatistics:")
        print(f"  Best MSE:  {best:.4f}")
        print(f"  Worst MSE: {worst:.4f}")
        print(f"  Average:   {avg:.4f}")
        print(f"  Trend:     {'↓' if trend < 0 else '↑'} {abs(trend):.4f} (first → last)")
    
    # Best submission details
    best_sub = min(submissions, key=lambda x: x["mse_score"])
    print(f"\n🏆 Best Submission (MSE={best_sub['mse_score']:.4f}):")
    print(f"   Config: {json.dumps(best_sub.get('config', {}), indent=2)}")
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    analyze_submissions()
