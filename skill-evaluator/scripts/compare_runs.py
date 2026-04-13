#!/usr/bin/env python3
"""Compare two evaluation runs and produce benchmark data.

Can aggregate a single run, or compare current vs previous for regression detection.

Usage:
    # Aggregate single run into benchmark
    python -m scripts.compare_runs <workspace-dir> --skill-name <name>

    # Compare two runs for regression
    python -m scripts.compare_runs <current-dir> <baseline-dir> --skill-name <name>

    # CI: fail on regression
    python -m scripts.compare_runs <current-dir> <baseline-dir> --no-regression
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from scripts.utils import calculate_stats


def load_run_results(benchmark_dir: Path) -> dict:
    """Load all run results from a benchmark directory.

    Returns dict keyed by config name, each containing a list of run results.
    """
    # Support both layouts: eval dirs directly, or under runs/
    runs_dir = benchmark_dir / "runs"
    if runs_dir.exists():
        search_dir = runs_dir
    elif list(benchmark_dir.glob("eval-*")):
        search_dir = benchmark_dir
    else:
        print(f"No eval directories found in {benchmark_dir}", file=sys.stderr)
        return {}

    results: dict[str, list] = {}

    for eval_idx, eval_dir in enumerate(sorted(search_dir.glob("eval-*"))):
        # Load eval metadata
        metadata_path = eval_dir / "eval_metadata.json"
        eval_id = eval_idx
        eval_name = eval_dir.name
        if metadata_path.exists():
            try:
                with open(metadata_path) as mf:
                    meta = json.load(mf)
                    eval_id = meta.get("eval_id", eval_idx)
                    eval_name = meta.get("eval_name", eval_dir.name)
            except (json.JSONDecodeError, OSError):
                pass

        for config_dir in sorted(eval_dir.iterdir()):
            if not config_dir.is_dir():
                continue
            # Skip non-config directories
            if not list(config_dir.glob("run-*")):
                continue
            config = config_dir.name
            if config not in results:
                results[config] = []

            for run_dir in sorted(config_dir.glob("run-*")):
                # Try to get run number from directory name
                try:
                    run_number = int(run_dir.name.split("-")[1])
                except (ValueError, IndexError):
                    # Use uuid-based run dir — assign sequential number
                    existing = [r for r in results.get(config, []) if r.get("_dir") == str(run_dir)]
                    run_number = len([r for r in results.get(config, []) if r.get("eval_id") == eval_id]) + 1

                grading_file = run_dir / "grading.json"
                if not grading_file.exists():
                    continue

                try:
                    with open(grading_file) as f:
                        grading = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"Warning: Invalid JSON in {grading_file}: {e}", file=sys.stderr)
                    continue

                result = {
                    "eval_id": eval_id,
                    "eval_name": eval_name,
                    "run_number": run_number,
                    "pass_rate": grading.get("summary", {}).get("pass_rate", 0.0),
                    "passed": grading.get("summary", {}).get("passed", 0),
                    "failed": grading.get("summary", {}).get("failed", 0),
                    "total": grading.get("summary", {}).get("total", 0),
                    "_dir": str(run_dir),
                }

                # Extract timing
                timing = grading.get("timing", {})
                result["time_seconds"] = timing.get("total_duration_seconds", 0.0)
                timing_file = run_dir / "timing.json"
                if result["time_seconds"] == 0.0 and timing_file.exists():
                    try:
                        with open(timing_file) as tf:
                            timing_data = json.load(tf)
                        result["time_seconds"] = timing_data.get("total_duration_seconds", 0.0)
                        result["tokens"] = timing_data.get("total_tokens", 0)
                    except json.JSONDecodeError:
                        pass

                # Extract metrics
                metrics = grading.get("execution_metrics", {})
                result["tool_calls"] = metrics.get("total_tool_calls", 0)
                if not result.get("tokens"):
                    result["tokens"] = metrics.get("output_chars", 0)
                result["errors"] = metrics.get("errors_encountered", 0)

                # Extract expectations
                result["expectations"] = grading.get("expectations", [])

                # Extract notes
                notes_summary = grading.get("user_notes_summary", {})
                notes = []
                notes.extend(notes_summary.get("uncertainties", []))
                notes.extend(notes_summary.get("needs_review", []))
                notes.extend(notes_summary.get("workarounds", []))
                result["notes"] = notes

                results[config].append(result)

    return results


def aggregate_results(results: dict) -> dict:
    """Aggregate run results into summary statistics."""
    run_summary = {}
    configs = list(results.keys())

    for config in configs:
        runs = results.get(config, [])
        if not runs:
            run_summary[config] = {
                "pass_rate": {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0},
                "time_seconds": {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0},
                "tokens": {"mean": 0, "stddev": 0, "min": 0, "max": 0},
            }
            continue

        pass_rates = [r["pass_rate"] for r in runs]
        times = [r["time_seconds"] for r in runs]
        tokens = [r.get("tokens", 0) for r in runs]

        run_summary[config] = {
            "pass_rate": calculate_stats(pass_rates),
            "time_seconds": calculate_stats(times),
            "tokens": calculate_stats(tokens),
        }

    # Calculate delta between first two configs
    if len(configs) >= 2:
        primary = run_summary.get(configs[0], {})
        baseline = run_summary.get(configs[1], {})
    else:
        primary = run_summary.get(configs[0], {}) if configs else {}
        baseline = {}

    delta_pr = primary.get("pass_rate", {}).get("mean", 0) - baseline.get("pass_rate", {}).get("mean", 0)
    delta_time = primary.get("time_seconds", {}).get("mean", 0) - baseline.get("time_seconds", {}).get("mean", 0)
    delta_tokens = primary.get("tokens", {}).get("mean", 0) - baseline.get("tokens", {}).get("mean", 0)

    run_summary["delta"] = {
        "pass_rate": f"{delta_pr:+.2f}",
        "time_seconds": f"{delta_time:+.1f}",
        "tokens": f"{delta_tokens:+.0f}",
    }

    return run_summary


def generate_benchmark(benchmark_dir: Path, skill_name: str = "") -> dict:
    """Generate complete benchmark.json from run results."""
    results = load_run_results(benchmark_dir)
    if not results:
        return {}
    run_summary = aggregate_results(results)

    # Build runs array
    runs = []
    for config in results:
        for result in results[config]:
            runs.append({
                "eval_id": result["eval_id"],
                "eval_name": result.get("eval_name", f"eval-{result['eval_id']}"),
                "configuration": config,
                "run_number": result["run_number"],
                "result": {
                    "pass_rate": result["pass_rate"],
                    "passed": result["passed"],
                    "failed": result["failed"],
                    "total": result["total"],
                    "time_seconds": result["time_seconds"],
                    "tokens": result.get("tokens", 0),
                    "tool_calls": result.get("tool_calls", 0),
                    "errors": result.get("errors", 0),
                },
                "expectations": result["expectations"],
                "notes": result["notes"],
            })

    eval_ids = sorted(set(r["eval_id"] for config in results.values() for r in config))

    return {
        "metadata": {
            "skill_name": skill_name or "<skill-name>",
            "skill_path": str(benchmark_dir),
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "evals_run": eval_ids,
        },
        "runs": runs,
        "run_summary": run_summary,
        "notes": [],
    }


def generate_markdown(benchmark: dict) -> str:
    """Generate human-readable benchmark.md."""
    metadata = benchmark["metadata"]
    run_summary = benchmark["run_summary"]
    configs = [k for k in run_summary if k != "delta"]

    lines = [
        f"# Skill Benchmark: {metadata['skill_name']}",
        "",
        f"**Date**: {metadata['timestamp']}",
        f"**Evals**: {', '.join(map(str, metadata['evals_run']))}",
        "",
        "## Summary",
        "",
    ]

    if len(configs) >= 2:
        label_a = configs[0].replace("_", " ").title()
        label_b = configs[1].replace("_", " ").title()
        delta = run_summary.get("delta", {})
        a_summary = run_summary.get(configs[0], {})
        b_summary = run_summary.get(configs[1], {})

        lines.extend([
            f"| Metric | {label_a} | {label_b} | Delta |",
            "|--------|----------|----------|-------|",
        ])

        # Pass rate
        a_pr = a_summary.get("pass_rate", {})
        b_pr = b_summary.get("pass_rate", {})
        lines.append(
            f"| Pass Rate | {a_pr.get('mean', 0)*100:.0f}% ± {a_pr.get('stddev', 0)*100:.0f}% "
            f"| {b_pr.get('mean', 0)*100:.0f}% ± {b_pr.get('stddev', 0)*100:.0f}% "
            f"| {delta.get('pass_rate', '—')} |"
        )

        # Time
        a_time = a_summary.get("time_seconds", {})
        b_time = b_summary.get("time_seconds", {})
        lines.append(
            f"| Time | {a_time.get('mean', 0):.1f}s ± {a_time.get('stddev', 0):.1f}s "
            f"| {b_time.get('mean', 0):.1f}s ± {b_time.get('stddev', 0):.1f}s "
            f"| {delta.get('time_seconds', '—')}s |"
        )

        # Tokens
        a_tok = a_summary.get("tokens", {})
        b_tok = b_summary.get("tokens", {})
        lines.append(
            f"| Tokens | {a_tok.get('mean', 0):.0f} ± {a_tok.get('stddev', 0):.0f} "
            f"| {b_tok.get('mean', 0):.0f} ± {b_tok.get('stddev', 0):.0f} "
            f"| {delta.get('tokens', '—')} |"
        )
    elif len(configs) == 1:
        label = configs[0].replace("_", " ").title()
        summary = run_summary.get(configs[0], {})
        pr = summary.get("pass_rate", {})
        tm = summary.get("time_seconds", {})
        tk = summary.get("tokens", {})

        lines.extend([
            f"| Metric | {label} |",
            "|--------|--------|",
            f"| Pass Rate | {pr.get('mean', 0)*100:.0f}% ± {pr.get('stddev', 0)*100:.0f}% |",
            f"| Time | {tm.get('mean', 0):.1f}s ± {tm.get('stddev', 0):.1f}s |",
            f"| Tokens | {tk.get('mean', 0):.0f} ± {tk.get('stddev', 0):.0f} |",
        ])

    if benchmark.get("notes"):
        lines.extend(["", "## Notes", ""])
        for note in benchmark["notes"]:
            lines.append(f"- {note}")

    return "\n".join(lines)


def compare_runs(current_dir: Path, baseline_dir: Path) -> dict:
    """Compare current run with baseline for regression detection."""
    current_results = load_run_results(current_dir)
    baseline_results = load_run_results(baseline_dir)

    # Compare with_skill configurations
    current_with = current_results.get("with_skill", [])
    baseline_with = baseline_results.get("with_skill", [])

    regressions = []
    improvements = []
    unchanged = []

    # Build lookup by eval_id
    baseline_by_eval = {}
    for r in baseline_with:
        baseline_by_eval.setdefault(r["eval_id"], []).append(r)

    current_by_eval = {}
    for r in current_with:
        current_by_eval.setdefault(r["eval_id"], []).append(r)

    for eval_id in set(list(baseline_by_eval.keys()) + list(current_by_eval.keys())):
        baseline_runs = baseline_by_eval.get(eval_id, [])
        current_runs = current_by_eval.get(eval_id, [])

        if not baseline_runs:
            continue

        baseline_avg = sum(r["pass_rate"] for r in baseline_runs) / len(baseline_runs) if baseline_runs else 0
        current_avg = sum(r["pass_rate"] for r in current_runs) / len(current_runs) if current_runs else 0

        diff = current_avg - baseline_avg

        entry = {
            "eval_id": eval_id,
            "baseline_pass_rate": round(baseline_avg, 4),
            "current_pass_rate": round(current_avg, 4),
            "delta": round(diff, 4),
        }

        if diff < -0.01:
            regressions.append(entry)
        elif diff > 0.01:
            improvements.append(entry)
        else:
            unchanged.append(entry)

    return {
        "regressions": regressions,
        "improvements": improvements,
        "unchanged": unchanged,
        "has_regression": len(regressions) > 0,
    }


def main():
    parser = argparse.ArgumentParser(description="Compare evaluation runs and produce benchmark data")
    parser.add_argument("dirs", nargs="+", type=Path, help="Workspace directories (1 for aggregate, 2 for comparison)")
    parser.add_argument("--skill-name", default="", help="Name of the skill being evaluated")
    parser.add_argument("--no-regression", action="store_true", help="CI: exit 1 if regression detected (requires 2 dirs)")
    args = parser.parse_args()

    if len(args.dirs) == 1:
        # Single dir: aggregate
        benchmark = generate_benchmark(args.dirs[0], args.skill_name)
        if not benchmark:
            print(f"No results found in {args.dirs[0]}", file=sys.stderr)
            sys.exit(1)

        # Write output
        json_path = args.dirs[0] / "benchmark.json"
        with open(json_path, "w") as f:
            json.dump(benchmark, f, indent=2)
        print(f"Generated: {json_path}")

        md = generate_markdown(benchmark)
        md_path = args.dirs[0] / "benchmark.md"
        md_path.write_text(md)
        print(f"Generated: {md_path}")
        print(md)

    elif len(args.dirs) >= 2:
        # Two dirs: compare for regression
        comparison = compare_runs(args.dirs[0], args.dirs[1])

        # Also generate benchmark for current run
        current_benchmark = generate_benchmark(args.dirs[0], args.skill_name)
        if current_benchmark:
            json_path = args.dirs[0] / "benchmark.json"
            with open(json_path, "w") as f:
                json.dump(current_benchmark, f, indent=2)

        print(json.dumps(comparison, indent=2))

        if args.no_regression and comparison.get("has_regression", False):
            for reg in comparison.get("regressions", []):
                print(
                    f"REGRESSION: eval-{reg['eval_id']} pass rate dropped from "
                    f"{reg['baseline_pass_rate']:.0%} to {reg['current_pass_rate']:.0%} "
                    f"(delta: {reg['delta']:+.0%})",
                    file=sys.stderr,
                )
            sys.exit(1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()