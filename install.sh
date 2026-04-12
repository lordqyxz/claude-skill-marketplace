#!/usr/bin/env bash
set -euo pipefail

MARKETPLACE_REPO="https://github.com/lordqyxz/claude-skill-marketplace"
CLAUDE_SKILLS_DIR="${HOME}/.claude/skills"
MARKETPLACE_DIR=""

cleanup() {
  if [[ -n "$MARKETPLACE_DIR" && -d "$MARKETPLACE_DIR" ]]; then
    rm -rf "$MARKETPLACE_DIR"
  fi
}
trap cleanup EXIT

# Clone or update the marketplace
MARKETPLACE_DIR=$(mktemp -d)
echo "Downloading marketplace..."
git clone --depth 1 "$MARKETPLACE_REPO" "$MARKETPLACE_DIR/repo" 2>/dev/null

SKILL_NAME="${1:-}"
if [[ -z "$SKILL_NAME" ]]; then
  echo "Available skills:"
  # Parse registry.json with python or basic grep
  if command -v python3 &>/dev/null; then
    python3 -c "
import json, sys
with open('$MARKETPLACE_DIR/repo/registry.json') as f:
    r = json.load(f)
for s in r['skills']:
    print(f\"  {s['name']:20s} {s['description']}\")
"
  else
    grep -A1 '"name"' "$MARKETPLACE_DIR/repo/registry.json" | grep -v schema | paste - - | sed 's/[",]//g' | awk '{print "  "$2}'
  fi
  echo ""
  echo "Usage: $0 <skill-name>"
  exit 0
fi

SKILL_DIR="$MARKETPLACE_DIR/repo/skills/$SKILL_NAME"

if [[ ! -d "$SKILL_DIR" ]]; then
  echo "Error: Skill '$SKILL_NAME' not found in marketplace."
  echo "Run '$0' without arguments to see available skills."
  exit 1
fi

# Confirm SKILL.md exists
if [[ ! -f "$SKILL_DIR/SKILL.md" ]]; then
  echo "Error: SKILL.md not found in '$SKILL_NAME'. Invalid skill."
  exit 1
fi

# Copy to Claude skills directory
mkdir -p "$CLAUDE_SKILLS_DIR"
TARGET_DIR="$CLAUDE_SKILLS_DIR/$SKILL_NAME"

if [[ -d "$TARGET_DIR" ]]; then
  echo "Warning: Skill '$SKILL_NAME' already installed. Updating..."
  rm -rf "$TARGET_DIR"
fi

cp -r "$SKILL_DIR" "$TARGET_DIR"
echo "Installed skill '$SKILL_NAME' to $TARGET_DIR"

# Remind about settings
echo ""
echo "To enable the skill, add it to ~/.claude/settings.json:"
echo '  "skills": { "'"$SKILL_NAME"'": true }'
echo ""
echo "Done!"