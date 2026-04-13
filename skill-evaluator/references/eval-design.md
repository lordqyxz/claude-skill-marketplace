# Writing Effective Eval Cases

Guide for creating eval cases that accurately measure skill performance.

## What Makes a Good Eval

A good eval case has three properties:

1. **Realistic prompt** — Something a real user would actually say, with context and specifics
2. **Verifiable assertions** — Statements that can be objectively checked as true/false
3. **Discriminating** — The assertion passes when the skill genuinely helps and fails when it doesn't

## Prompt Writing

### Good prompts

```
写一个 Python 函数，批量处理 CSV 文件，按指定列分组并计算每组的统计信息（均值、中位数、标准差），结果保存为新的 CSV
```

Why: Concrete task, specific requirements, realistic use case.

### Bad prompts

```
写一个数据处理函数
```

Why: Too vague, no way to evaluate if the output is correct.

**Rules:**
- Include enough detail that a correct output is clearly distinguishable from a wrong one
- Specify the domain/problem, not the solution approach
- Use realistic scenarios with backstory, not abstract requests

## Assertion Writing

### Discriminating assertions

Good assertions are **hard to satisfy without actually doing the work correctly**:

```json
"Statistical result structure uses dataclass or NamedTuple"
```

This is discriminating because Claude without the skill will typically use raw dicts.

### Non-discriminating assertions

Avoid assertions that pass regardless of skill usage:

```json
"The code runs without errors"
```

This is non-discriminating because both with-skill and without-skill runs may produce working code.

### Assertion patterns that work well

| Pattern | Example | Why it works |
|---------|---------|-------------|
| Idiomatic choice | "Uses pathlib.Path instead of os.path" | Skill-specific guidance |
| Structural requirement | "Business logic separated from I/O" | Requires understanding, not just compliance |
| Error handling | "Invalid input raises ValueError with actual value" | Without skill, errors are often silently handled |
| Design pattern | "Uses observer pattern for change notifications" | Specific architecture guidance |

### Assertion patterns to avoid

| Pattern | Example | Why it fails |
|---------|---------|-------------|
| Too generic | "Code is well-written" | Subjective, can't verify |
| Trivially satisfied | "A function exists" | Any solution will have functions |
| Solution-specific | "Function is named process_csv" | Overfit to one approach |

## How Many Evals

- **Minimum**: 2-3 eval cases for initial validation
- **Recommended**: 5-8 eval cases covering different scenarios
- **Comprehensive**: 10+ with edge cases and varied difficulty

Each eval should have 4-8 assertions. Fewer means low resolution; more means diminishing returns.

## evals.json Format

```json
{
  "skill_name": "your-skill-name",
  "evals": [
    {
      "id": 1,
      "prompt": "Realistic user prompt with specifics",
      "expected_output": "Description of what a good result looks like",
      "files": [],
      "assertions": [
        "Specific, verifiable statement about the output",
        "Another statement checking a different aspect"
      ]
    }
  ]
}
```

## Iterative Improvement

Start with a few evals, run them, and see what happens:

1. If an assertion always passes in both configs → make it more discriminating or replace it
2. If an assertion always fails → check if it's testing something the skill actually promises
3. If you notice an important quality difference that no assertion catches → add one
4. If an eval produces wildly different results each run → it may be too open-ended