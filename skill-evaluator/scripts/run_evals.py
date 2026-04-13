#!/usr/bin/env python3
"""Run quality evaluation for a skill.

Executes eval prompts with and without the skill, captures outputs and timing,
then grades the results against assertions.

Usage:
    python -m scripts.run_evals <skill-path> [options]

Options:
    --runs-per-eval N    Number of runs per eval per configuration (default: 3)
    --timeout SECONDS    Timeout per run in seconds (default: 120)
    --model MODEL        Model to use for claude -p
    --output-dir DIR     Override output directory (default: <skill-name>-workspace/<timestamp>)
    --no-baseline        Skip without-skill baseline runs
    --min-pass-rate RATE Minimum pass rate threshold for CI (0.0-1.0)
    --verbose            Print progress to stderr
"""

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from typing import Optional

from scripts.utils import parse_skill_md, load_evals, find_project_root


def run_single_eval(
    prompt: str,
    skill_name: str,
    skill_description: str,
    skill_path: str,
    with_skill: bool,
    timeout: int,
    project_root: str,
    output_dir: Path,
    model: Optional[str] = None,
) -> dict:
    """Run a single eval prompt and capture results.

    Uses claude -p to execute the prompt. For with-skill runs, creates a
    temporary command file so Claude sees the skill. Captures stream-json
    output to extract the transcript and tool calls.
    """
    run_id = uuid.uuid4().hex[:8]
    run_dir = output_dir / f"run-{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir = run_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    # For with-skill runs, create a temporary command file
    command_file = None
    clean_name = None

    if with_skill:
        clean_name = f"{skill_name}-skill-{run_id}"
        project_commands_dir = Path(project_root) / ".claude" / "commands"
        command_file = project_commands_dir / f"{clean_name}.md"

        try:
            project_commands_dir.mkdir(parents=True, exist_ok=True)
            indented_desc = "\n  ".join(skill_description.split("\n"))
            # Point to the actual skill file for Claude to read
            command_content = (
                f"---\n"
                f"description: |\n"
                f"  {indented_desc}\n"
                f"---\n\n"
                f"# {skill_name}\n\n"
                f"Read and follow the instructions in {skill_path}/SKILL.md\n"
            )
            command_file.write_text(command_content)
        except OSError as e:
            print(f"Warning: could not create command file: {e}", file=sys.stderr)

    # Build claude -p command
    cmd = [
        "claude",
        "-p", prompt,
        "--output-format", "stream-json",
        "--verbose",
    ]
    if model:
        cmd.extend(["--model", model])

    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    start_time = time.time()
    total_tokens = 0
    transcript_lines = []
    tool_calls_count = 0
    files_created = []

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=project_root,
            env=env,
        )

        buffer = ""
        while True:
            if process.poll() is not None:
                remaining = process.stdout.read()
                if remaining:
                    buffer += remaining.decode("utf-8", errors="replace")
                break

            import select
            ready, _, _ = select.select([process.stdout], [], [], 1.0)
            if not ready:
                if time.time() - start_time > timeout:
                    process.kill()
                    process.wait()
                    break
                continue

            chunk = os.read(process.stdout.fileno(), 8192)
            if not chunk:
                break
            buffer += chunk.decode("utf-8", errors="replace")

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    transcript_lines.append(line)
                    continue

                # Extract assistant messages for transcript
                if event.get("type") == "assistant":
                    message = event.get("message", {})
                    for content_item in message.get("content", []):
                        if content_item.get("type") == "text":
                            transcript_lines.append(content_item.get("text", ""))
                        elif content_item.get("type") == "tool_use":
                            tool_calls_count += 1
                            tool_name = content_item.get("name", "")
                            tool_input = content_item.get("input", {})
                            # Track file creation
                            if tool_name == "Write":
                                fp = tool_input.get("file_path", "")
                                if fp:
                                    files_created.append(fp)
                            transcript_lines.append(
                                f"[Tool: {tool_name}] {json.dumps(tool_input, ensure_ascii=False)[:200]}"
                            )

                # Extract token usage from result
                elif event.get("type") == "result":
                    result = event.get("result", "")
                    if isinstance(result, str):
                        transcript_lines.append(result)
                    usage = event.get("usage", {})
                    total_tokens = usage.get("total_tokens", 0)

    except Exception as e:
        transcript_lines.append(f"[ERROR] {e}")
    finally:
        if command_file and command_file.exists():
            try:
                command_file.unlink()
            except OSError:
                pass
        if process.poll() is None:
            process.kill()
            process.wait()

    duration_ms = int((time.time() - start_time) * 1000)

    # Save transcript
    transcript_path = run_dir / "transcript.md"
    transcript_content = "\n\n".join(transcript_lines) if transcript_lines else "(no output captured)"
    transcript_path.write_text(transcript_content)

    # Save timing
    timing = {
        "total_tokens": total_tokens,
        "duration_ms": duration_ms,
        "total_duration_seconds": round(duration_ms / 1000, 1),
    }
    (run_dir / "timing.json").write_text(json.dumps(timing, indent=2))

    # Save metrics
    metrics = {
        "tool_calls": tool_calls_count,
        "files_created": [str(f) for f in files_created],
        "output_chars": sum(len(str(t)) for t in transcript_lines),
        "transcript_chars": len(transcript_content),
    }
    (outputs_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))

    return {
        "run_dir": str(run_dir),
        "timing": timing,
        "metrics": metrics,
    }


def main():
    parser = argparse.ArgumentParser(description="Run quality evaluation for a skill")
    parser.add_argument("skill_path", type=Path, help="Path to the skill directory")
    parser.add_argument("--runs-per-eval", type=int, default=3, help="Runs per eval per config (default: 3)")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout per run in seconds (default: 120)")
    parser.add_argument("--model", default=None, help="Model to use for claude -p")
    parser.add_argument("--output-dir", type=Path, default=None, help="Override output directory")
    parser.add_argument("--no-baseline", action="store_true", help="Skip baseline (without-skill) runs")
    parser.add_argument("--min-pass-rate", type=float, default=None, help="CI: minimum pass rate threshold (0-1)")
    parser.add_argument("--verbose", action="store_true", help="Print progress to stderr")
    args = parser.parse_args()

    skill_path = args.skill_path.resolve()

    if not (skill_path / "SKILL.md").exists():
        print(f"Error: No SKILL.md found at {skill_path}", file=sys.stderr)
        sys.exit(1)

    # Load skill metadata
    name, description, content = parse_skill_md(skill_path)

    # Load evals
    evals = load_evals(skill_path)
    if not evals:
        print(f"Error: No evals found for skill '{name}'. Create evals/evals.json first.", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"Skill: {name}", file=sys.stderr)
        print(f"Evals: {len(evals)} test cases", file=sys.stderr)
        print(f"Runs per eval: {args.runs_per_eval}", file=sys.stderr)

    # Determine output directory
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if args.output_dir:
        output_base = args.output_dir
    else:
        output_base = skill_path.parent / f"{name}-workspace" / timestamp
    output_base.mkdir(parents=True, exist_ok=True)

    project_root = find_project_root()
    all_results = []

    # Run each eval
    for eval_idx, eval_case in enumerate(evals):
        eval_id = eval_case.get("id", eval_idx)
        eval_prompt = eval_case.get("prompt", "")
        expectations = eval_case.get("assertions", eval_case.get("expectations", []))

        if args.verbose:
            print(f"\nEval {eval_id}: {eval_prompt[:60]}...", file=sys.stderr)

        eval_dir = output_base / f"eval-{eval_id}"
        eval_dir.mkdir(parents=True, exist_ok=True)

        # Save eval metadata
        eval_metadata = {
            "eval_id": eval_id,
            "eval_name": eval_case.get("expected_output", "")[:50] if eval_case.get("expected_output") else f"eval-{eval_id}",
            "prompt": eval_prompt,
            "assertions": expectations,
        }
        (eval_dir / "eval_metadata.json").write_text(json.dumps(eval_metadata, indent=2, ensure_ascii=False))

        # Run with skill
        with_skill_dir = eval_dir / "with_skill"
        with_skill_dir.mkdir(exist_ok=True)

        for run_num in range(1, args.runs_per_eval + 1):
            if args.verbose:
                print(f"  with_skill run {run_num}/{args.runs_per_eval}", file=sys.stderr)
            result = run_single_eval(
                prompt=eval_prompt,
                skill_name=name,
                skill_description=description,
                skill_path=str(skill_path),
                with_skill=True,
                timeout=args.timeout,
                project_root=str(project_root),
                output_dir=with_skill_dir,
                model=args.model,
            )
            all_results.append({
                "eval_id": eval_id,
                "configuration": "with_skill",
                **result,
            })

        # Run without skill (baseline)
        if not args.no_baseline:
            without_skill_dir = eval_dir / "without_skill"
            without_skill_dir.mkdir(exist_ok=True)

            for run_num in range(1, args.runs_per_eval + 1):
                if args.verbose:
                    print(f"  without_skill run {run_num}/{args.runs_per_eval}", file=sys.stderr)
                result = run_single_eval(
                    prompt=eval_prompt,
                    skill_name=name,
                    skill_description=description,
                    skill_path=str(skill_path),
                    with_skill=False,
                    timeout=args.timeout,
                    project_root=str(project_root),
                    output_dir=without_skill_dir,
                    model=args.model,
                )
                all_results.append({
                    "eval_id": eval_id,
                    "configuration": "without_skill",
                    **result,
                })

    # Save run manifest
    manifest = {
        "skill_name": name,
        "skill_path": str(skill_path),
        "timestamp": timestamp,
        "runs_per_eval": args.runs_per_eval,
        "model": args.model or "default",
        "total_runs": len(all_results),
        "results": all_results,
    }
    (output_base / "run_manifest.json").write_text(json.dumps(manifest, indent=2))

    if args.verbose:
        print(f"\nResults saved to: {output_base}", file=sys.stderr)
        print(f"Total runs: {len(all_results)}", file=sys.stderr)
        print(f"\nNext steps:", file=sys.stderr)
        print(f"  1. Grade results: spawn grader subagent for each run directory", file=sys.stderr)
        print(f"  2. Aggregate: python -m scripts.compare_runs {output_base}", file=sys.stderr)

    # CI: check minimum pass rate if grading is already done
    if args.min_pass_rate is not None:
        # Look for grading.json files
        graded_runs = []
        for eval_dir in sorted(output_base.glob("eval-*")):
            for config_dir in eval_dir.iterdir():
                if not config_dir.is_dir():
                    continue
                for run_dir in sorted(config_dir.glob("run-*")):
                    grading_file = run_dir / "grading.json"
                    if grading_file.exists():
                        with open(grading_file) as f:
                            grading = json.load(f)
                        graded_runs.append(grading.get("summary", {}).get("pass_rate", 0.0))

        if graded_runs:
            avg_pass_rate = sum(graded_runs) / len(graded_runs)
            if args.verbose:
                print(f"Average pass rate: {avg_pass_rate:.2f} (threshold: {args.min_pass_rate})", file=sys.stderr)
            if avg_pass_rate < args.min_pass_rate:
                print(f"FAIL: pass rate {avg_pass_rate:.2f} < threshold {args.min_pass_rate}", file=sys.stderr)
                sys.exit(1)
            else:
                print(f"PASS: pass rate {avg_pass_rate:.2f} >= threshold {args.min_pass_rate}", file=sys.stderr)


if __name__ == "__main__":
    main()