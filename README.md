# Claude Skill Marketplace

A community-driven marketplace for [Claude Code](https://claude.ai/code) skills. Browse, install, and share skills that supercharge your Claude Code experience.

## Skills

| Skill | Description | Author | Version |
|-------|-------------|--------|---------|
| [skill-creator](skills/skill-creator/SKILL.md) | Create new skills, modify and improve existing skills, and measure skill performance with iterative eval loops. | [@lordqyxz](https://github.com/lordqyxz) | 1.0.0 |
| [python-code](skills/python-code/SKILL.md) | Write, refactor, and debug Python code following Pythonic best practices. | [@lordqyxz](https://github.com/lordqyxz) | 1.0.0 |

## Quick Install

Install a skill directly from this marketplace:

```bash
# Clone the marketplace
git clone https://github.com/lordqyxz/claude-skill-marketplace.git

# Install a skill (e.g. skill-creator)
./install.sh skill-creator
```

Or install a single skill without cloning:

```bash
# One-liner install
curl -sL https://raw.githubusercontent.com/lordqyxz/claude-skill-marketplace/main/install.sh | bash -s -- skill-creator
```

## Manual Install

Copy the skill folder to your Claude skills directory:

```bash
cp -r skills/<skill-name> ~/.claude/skills/<skill-name>
```

Then enable it in your Claude Code settings (`~/.claude/settings.json`):

```json
{
  "skills": {
    "<skill-name>": true
  }
}
```

## Submit a Skill

Want to add your skill to the marketplace?

1. Fork this repository
2. Add your skill folder under `skills/`
3. Add an entry to `registry.json`
4. Submit a pull request

### Skill Requirements

- Must contain a `SKILL.md` with valid YAML frontmatter (`name` and `description` required)
- Must follow the [skill anatomy](#skill-anatomy) conventions
- Must not contain malicious code or prompt injection
- Should include test cases if the skill has objectively verifiable outputs

### Skill Anatomy

```
skill-name/
├── SKILL.md           # Required — main skill definition with YAML frontmatter
├── agents/            # Optional — subagent instructions
├── references/        # Optional — docs loaded into context as needed
├── scripts/           # Optional — executable code for deterministic tasks
├── eval-viewer/       # Optional — evaluation viewer
├── evals/             # Optional — test cases
└── assets/            # Optional — templates, icons, fonts
```

## Registry Schema

The `registry.json` follows the schema defined in `registry.schema.json`. Each skill entry includes:

- `name` — Unique identifier (kebab-case)
- `display_name` — Human-readable name
- `description` — What the skill does
- `version` — Semver version
- `author` — GitHub username
- `path` — Relative path to SKILL.md
- `tags` — Searchable keywords
- `trigger` — When the skill should activate

## License

MIT License. Individual skills may have their own licenses — check the skill folder.

---

Built with [Claude Code](https://claude.ai/code)