---
name: skill-evaluator
description: Evaluate and benchmark Claude Code skills. Run structural validation, trigger accuracy tests, quality evals with automated grading, regression tracking across versions, and generate comprehensive reports. Use when users want to test a skill, benchmark skill performance, compare two skill versions, check skill health, or run CI-style evals.
---

# Skill Evaluator

A focused skill for evaluating and benchmarking other Claude Code skills.

Unlike skill-creator (which is a full lifecycle tool for creating → eval → improve), skill-evaluator is purely about **measurement**: validate structure, run evals, grade outputs, track regressions, and produce reports.

## Quick Reference

| Command | What it does |
|---------|-------------|
| `python -m scripts.validate_skill <skill-path>` | Structural validation |
| `python -m scripts.run_evals <skill-path>` | Run quality evals end-to-end |
| `python -m scripts.compare_runs <run-a> <run-b>` | Compare two evaluation runs |

## Evaluation Workflow

There are three evaluation modes, from lightest to deepest:

### Mode 1: Structural Validation

Fast, zero-cost check. Validates SKILL.md format, frontmatter, naming, and directory structure.

```bash
python -m scripts.validate_skill <skill-path>
```

This checks:
- SKILL.md exists with valid YAML frontmatter
- `name` is kebab-case, ≤64 chars
- `description` is ≤1024 chars, no angle brackets
- Only allowed frontmatter properties
- Directory structure follows conventions (agents/, scripts/, references/)

Returns exit code 0 on pass, 1 on fail. Output is JSON for CI integration.

### Mode 2: Trigger Evaluation

Tests whether the skill's description causes Claude to trigger correctly. This reuses the trigger eval infrastructure from skill-creator — if you need trigger eval, read `skill-creator/references/description-optimization.md` and run:

```bash
python -m skill-creator.scripts.run_eval --eval-set <path> --skill-path <skill-path>
```

### Mode 3: Quality Evaluation

The core mode. Runs skill against eval prompts, captures outputs, grades assertions, and produces benchmark data.

**Prerequisites:** The target skill must have `evals/evals.json` with test cases defined. If none exists, help the user create one first (see `references/eval-design.md`).

#### Step 1: Run evals

```bash
python -m scripts.run_evals <skill-path> \
  --runs-per-eval 3 \
  --timeout 120 \
  --model claude-sonnet-4-20250514
```

This runs each eval prompt:
- **With skill**: Claude has access to the skill, executes the prompt
- **Without skill** (baseline): Same prompt, no skill available

Results go to `<skill-name>-workspace/` sibling to the skill directory:
```
workspace/
  <timestamp>/
    eval-0/
      eval_metadata.json
      with_skill/
        run-1/
          transcript.md
          outputs/
          grading.json
          timing.json
      without_skill/
        run-1/
          transcript.md
          outputs/
          grading.json
          timing.json
    benchmark.json
    benchmark.md
```

#### Step 2: Grade results

After runs complete, each run is graded by spawning a grader subagent that evaluates assertions against the transcript and outputs. Read `agents/grader.md` for grading instructions.

For assertions that can be checked programmatically, write and run a script rather than using a subagent — scripts are faster, more reliable, and reusable.

#### Step 3: Aggregate and analyze

```bash
python -m scripts.compare_runs <workspace>/<timestamp> --skill-name <name>
```

This produces:
- `benchmark.json` with statistical aggregates (mean/stddev/min/max)
- `benchmark.md` with human-readable summary
- Delta between with-skill and without-skill configurations

Then do an analyst pass — read `agents/analyzer.md` and surface patterns the aggregate stats hide: non-discriminating assertions, high-variance evals, time/token tradeoffs.

#### Step 4: Report results

Present the evaluation results to the user. Key things to highlight:
- **Overall pass rate**: with_skill vs without_skill, with delta
- **Per-eval breakdown**: Which evals the skill helps most/least
- **Discriminating assertions**: Which assertions differentiate skill value
- **Non-discriminating assertions**: Which always pass or always fail (consider revising)
- **Time/token cost**: What the skill costs in resources
- **Recommendations**: Concrete next steps

Optionally, use the eval viewer from skill-creator:
```bash
python <skill-creator-path>/eval-viewer/generate_review.py <workspace>/<timestamp> \
  --skill-name <name> \
  --benchmark <workspace>/<timestamp>/benchmark.json
```

## Regression Tracking

Compare current results with a previous run to detect regressions:

```bash
python -m scripts.compare_runs <current-workspace> <previous-workspace>
```

This produces a diff report showing:
- Pass rate changes per eval
- New failures vs fixed issues
- Timing/token changes
- Assertion-level regression details

## Comparing Two Skill Versions

To compare two versions of a skill (e.g., before and after changes):

1. Run evals on version A: `python -m scripts.run_evals <skill-a-path> --output-dir workspace/version-a`
2. Run evals on version B: `python -m scripts.run_evals <skill-b-path> --output-dir workspace/version-b`
3. Compare: `python -m scripts.compare_runs workspace/version-a workspace/version-b`

For rigorous blind comparison, read `agents/grader.md` for the blind A/B protocol.

## CI Integration

All scripts support JSON output and exit codes for CI:

```bash
# Validate structure (exit 0 = pass)
python -m scripts.validate_skill <skill-path> --format json

# Run evals and check threshold (exit 0 = pass rate ≥ threshold)
python -m scripts.run_evals <skill-path> --min-pass-rate 0.7

# Compare with baseline (exit 0 = no regression)
python -m scripts.compare_runs <current> <baseline> --no-regression
```

## Communicating with the User

Adapt your language to the user's familiarity with evaluation jargon. When in doubt, briefly explain terms:
- "pass rate" → the fraction of assertions that passed (e.g., 5/6 = 83%)
- "assertion" → a specific check on the output (e.g., "uses pathlib not os.path")
- "baseline" → running without the skill, to measure what the skill actually adds
- "regression" → a result getting worse compared to a previous run

## Reference Files

Read these when the relevant topic comes up:

- `agents/grader.md` — How to evaluate assertions against outputs
- `agents/analyzer.md` — How to analyze benchmark patterns
- `references/eval-design.md` — How to write good eval cases
- `skill-creator/references/schemas.md` — JSON schemas for eval data structures