#!/usr/bin/env python3
"""Validate a skill's structure and metadata.

Checks SKILL.md format, frontmatter, naming conventions, and directory layout.
Returns exit code 0 on pass, 1 on fail.

Usage:
    python -m scripts.validate_skill <skill-path> [--format json|text]
"""

import argparse
import json
import sys
from pathlib import Path

from scripts.utils import parse_skill_md, is_kebab_case


ALLOWED_FRONTMATTER = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_COMPATIBILITY_LENGTH = 500


def validate_skill(skill_path: Path) -> list[dict]:
    """Validate a skill directory and return list of issues.

    Each issue has: severity (error|warning), field, message.
    """
    issues = []

    # Check SKILL.md exists
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        issues.append({
            "severity": "error",
            "field": "SKILL.md",
            "message": "SKILL.md not found",
        })
        return issues  # Can't continue without SKILL.md

    # Parse frontmatter
    try:
        name, description, content = parse_skill_md(skill_path)
    except ValueError as e:
        issues.append({
            "severity": "error",
            "field": "SKILL.md",
            "message": str(e),
        })
        return issues

    # Validate name
    if not name:
        issues.append({
            "severity": "error",
            "field": "name",
            "message": "name is required in frontmatter",
        })
    else:
        if not is_kebab_case(name):
            issues.append({
                "severity": "error",
                "field": "name",
                "message": f"name must be kebab-case, got: '{name}'",
            })
        if len(name) > MAX_NAME_LENGTH:
            issues.append({
                "severity": "error",
                "field": "name",
                "message": f"name must be ≤{MAX_NAME_LENGTH} chars, got {len(name)}",
            })

    # Validate description
    if not description:
        issues.append({
            "severity": "error",
            "field": "description",
            "message": "description is required in frontmatter",
        })
    else:
        if len(description) > MAX_DESCRIPTION_LENGTH:
            issues.append({
                "severity": "error",
                "field": "description",
                "message": f"description must be ≤{MAX_DESCRIPTION_LENGTH} chars, got {len(description)}",
            })
        if "<" in description or ">" in description:
            issues.append({
                "severity": "error",
                "field": "description",
                "message": "description must not contain angle brackets (<>)",
            })

    # Check for unknown frontmatter properties
    lines = content.split("\n")
    if lines[0].strip() == "---":
        end_idx = None
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                end_idx = i
                break
        if end_idx:
            for line in lines[1:end_idx]:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    key = stripped.split(":")[0].strip()
                    if key and key not in ALLOWED_FRONTMATTER:
                        issues.append({
                            "severity": "warning",
                            "field": key,
                            "message": f"unknown frontmatter property '{key}'",
                        })

    # Validate compatibility field if present
    # Re-parse to get compatibility
    for line in lines[1:end_idx] if end_idx else []:
        if line.strip().startswith("compatibility:"):
            value = line.strip()[len("compatibility:"):].strip().strip('"').strip("'")
            if len(value) > MAX_COMPATIBILITY_LENGTH:
                issues.append({
                    "severity": "error",
                    "field": "compatibility",
                    "message": f"compatibility must be ≤{MAX_COMPATIBILITY_LENGTH} chars, got {len(value)}",
                })

    # Check evals directory structure
    evals_dir = skill_path / "evals"
    if evals_dir.exists():
        evals_json = evals_dir / "evals.json"
        if not evals_json.exists():
            issues.append({
                "severity": "warning",
                "field": "evals",
                "message": "evals/ directory exists but no evals.json found",
            })
        else:
            try:
                with open(evals_json) as f:
                    data = json.load(f)
                if "skill_name" not in data:
                    issues.append({
                        "severity": "warning",
                        "field": "evals.json",
                        "message": "missing 'skill_name' field",
                    })
                if "evals" not in data or not data["evals"]:
                    issues.append({
                        "severity": "warning",
                        "field": "evals.json",
                        "message": "no eval cases defined",
                    })
            except json.JSONDecodeError as e:
                issues.append({
                    "severity": "error",
                    "field": "evals.json",
                    "message": f"invalid JSON: {e}",
                })

    # Check agents directory
    agents_dir = skill_path / "agents"
    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.md"):
            content_check = agent_file.read_text()
            if len(content_check.strip()) < 50:
                issues.append({
                    "severity": "warning",
                    "field": f"agents/{agent_file.name}",
                    "message": "agent instruction file is very short (<50 chars), may be incomplete",
                })

    # Check scripts directory
    scripts_dir = skill_path / "scripts"
    if scripts_dir.exists():
        for script_file in scripts_dir.glob("*.py"):
            text = script_file.read_text()
            if "if __name__" not in text and script_file.name != "__init__.py" and script_file.name != "utils.py":
                issues.append({
                    "severity": "warning",
                    "field": f"scripts/{script_file.name}",
                    "message": "Python script has no if __name__ == '__main__' block (may not be directly runnable)",
                })

    return issues


def format_text(issues: list[dict], skill_path: str) -> str:
    """Format issues as human-readable text."""
    errors = [i for i in issues if i["severity"] == "error"]
    warnings = [i for i in issues if i["severity"] == "warning"]

    lines = [f"Validating: {skill_path}", ""]

    if not issues:
        lines.append("All checks passed.")
    else:
        for issue in issues:
            icon = "X" if issue["severity"] == "error" else "!"
            lines.append(f"  [{icon}] {issue['field']}: {issue['message']}")

        lines.append("")
        lines.append(f"  {len(errors)} error(s), {len(warnings)} warning(s)")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Validate a skill's structure and metadata")
    parser.add_argument("skill_path", type=Path, help="Path to the skill directory")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args()

    if not args.skill_path.exists():
        print(f"Error: path not found: {args.skill_path}", file=sys.stderr)
        sys.exit(1)

    issues = validate_skill(args.skill_path)

    if args.format == "json":
        output = {
            "skill_path": str(args.skill_path),
            "valid": not any(i["severity"] == "error" for i in issues),
            "errors": [i for i in issues if i["severity"] == "error"],
            "warnings": [i for i in issues if i["severity"] == "warning"],
            "total_issues": len(issues),
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_text(issues, str(args.skill_path)))

    # Exit with error if any errors found
    if any(i["severity"] == "error" for i in issues):
        sys.exit(1)


if __name__ == "__main__":
    main()