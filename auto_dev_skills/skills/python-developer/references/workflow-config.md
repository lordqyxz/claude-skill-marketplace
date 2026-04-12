# 工作流配置

## 工作流配置文件

将以下 JSON 保存为 `.claude/workflow-config.json`：

```json
{
  "version": "2.0",
  "mode": "semi-automatic",

  "steps": {
    "requirement_analysis": {
      "enabled": true,
      "use_script": false,
      "notes": "LLM 阶段，脚本无法理解自然语言"
    },
    "ddd_analysis": {
      "enabled": true,
      "use_script": true,
      "script": "scripts/analyze-domain.py",
      "notes": "脚本分析现有代码 + LLM 设计新模型"
    },
    "interface_design": {
      "enabled": true,
      "use_script": false,
      "notes": "LLM 阶段，需要设计决策"
    },
    "parallel_implementation": {
      "enabled": true,
      "agents": 3,
      "auto_format": true,
      "notes": "PostToolUse hook 自动格式化 + Agent 并行"
    },
    "quality_check": {
      "enabled": true,
      "use_script": true,
      "scripts": [
        "scripts/quality-check.sh",
        "scripts/verify-architecture.py"
      ],
      "skills": ["simplify", "test-cases"],
      "notes": "脚本验证优先 (零 token)，通过后 LLM 辅助审查"
    },
    "documentation_update": {
      "enabled": true,
      "use_skill": true,
      "skill": "update-docs"
    }
  },

  "confirmation": {
    "after_each_step": true,
    "before_apply_changes": true
  }
}
```

## PostToolUse Hook 自动格式化配置

将以下配置添加到 `.claude/settings.json` 的 `hooks.PostToolUse` 中：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_response.filePath // .tool_input.file_path' | { read -r f; if [[ \"$f\" == *.py ]]; then uv run ruff format \"$f\" 2>/dev/null && uv run ruff check --fix \"$f\" 2>/dev/null; fi; } || true",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

每次 Write/Edit Python 文件后，hook 自动运行 `ruff format` 和 `ruff check --fix`（零干预、零 token）。