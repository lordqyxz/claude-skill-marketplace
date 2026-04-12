# Auto Dev Skills

A community-driven marketplace for [Claude Code](https://claude.ai/code) skills. Browse, install, and share skills that supercharge your Claude Code experience.

## Skills

| Skill | Description | Author | Version |
|-------|-------------|--------|---------|
| [skill-creator](auto_dev_skills/skills/skill-creator/SKILL.md) | Create new skills, modify and improve existing skills, and measure skill performance with iterative eval loops. | [@lordqyxz](https://github.com/lordqyxz) | 1.0.0 |
| [python-code](auto_dev_skills/skills/python-code/SKILL.md) | Write, refactor, and debug Python code. PEP 8 + Effective Python + Fluent Python best practices (merged with effective-python). | [@lordqyxz](https://github.com/lordqyxz) | 2.0.0 |
| [vue3-sfc](auto_dev_skills/skills/vue3-sfc/SKILL.md) | Vue 3 SFC development, modification, and review with Composition API + script setup. | [@lordqyxz](https://github.com/lordqyxz) | 1.0.0 |
| [python-developer](auto_dev_skills/skills/python-developer/SKILL.md) | Structured Python development workflow with DDD and Clean Architecture. Delegates code implementation to python-code. | [@lordqyxz](https://github.com/lordqyxz) | 2.0.0 |

## Install

Install all skills via pip:

```bash
pip install auto-dev-skills && auto-dev-skills-install
```

Then enable skills in your Claude Code settings (`~/.claude/settings.json`):

```json
{
  "skills": {
    "skill-creator": true,
    "python-code": true,
    "python-developer": true,
    "vue3-sfc": true
  }
}
```

## Manual Install

Copy a skill folder to your Claude skills directory:

```bash
cp -r auto_dev_skills/skills/<skill-name> ~/.claude/skills/<skill-name>
```

## Submit a Skill

Want to add your skill to the marketplace?

1. Fork this repository
2. Add your skill folder under `auto_dev_skills/skills/`
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
