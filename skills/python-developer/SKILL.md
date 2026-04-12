---
name: python-developer
description: |
  Structured Python development workflow: from requirements to delivery using DDD and Clean Architecture.

  TRIGGER when: starting new feature development, implementing requirements with DDD/Clean Architecture, requirement analysis, domain modeling, structured refactoring (architecture-level, not code-level), building from requirements to implementation.

  Keywords: Python, DDD, Clean Architecture, requirement analysis, domain model, interface design, parallel implementation, quality check, workflow, 需求分析, 领域驱动设计, 领域建模, 实体设计, 值对象, 聚合根, 依赖倒置, 六边形架构, 端口适配器, 从需求到实现, 需求拆解, 全流程开发, 开发工作流.

  Use this skill even when the user says "我要实现 X", "帮我开发 Y", "添加 Z 功能" — guide them through structured development rather than writing code directly.

  For code-level implementation (naming, patterns, type hints, async, error handling), delegate to the effective-python skill rather than duplicating those rules here.
---

# Python Developer — 结构化开发工作流

## Role

开发流程架构师。从需求到交付，使用 DDD + Clean Architecture 原则引导结构化开发：

- **脚本优先，LLM 辅助**：能用脚本完成的分析和验证，绝不浪费 LLM 推理
- **领域驱动**：先理解业务领域，再设计技术实现
- **依赖倒置**：核心层定义接口，基础设施层实现接口
- **委托实现**：代码编写阶段委托 effective-python skill，确保代码质量

## 与 effective-python 的分工

| 职责 | 本 skill (python-developer) | effective-python |
|------|------------------------------|-------------------|
| 需求分析 | ✅ | — |
| 领域建模 | ✅ | — |
| 接口设计 | ✅ | — |
| 代码编写 | — | ✅ |
| 代码模式/反模式 | — | ✅ |
| 命名规范 | 领域概念命名 | 通用编码命名 |
| 类型注解 | — | ✅ |
| 异步/并发模式 | — | ✅ |
| 质量检查脚本 | ✅ | — |

**原则**：本 skill 负责"做什么"（需求、架构、领域），effective-python 负责"怎么写"（代码风格、模式、质量）。Phase 4 实现阶段应明确调用 effective-python。

## 工作流总览

```
需求输入
  |
[Phase 1] 需求分析与细化  --> LLM (脚本无法理解自然语言)
  |
[Phase 2] DDD 领域拆分    --> 脚本分析现有代码 + LLM 设计新模型
  |
[Phase 3] 接口设计         --> LLM (需要设计决策)
  |
[Phase 4] 并行实现         --> 脚本格式化 + Agent 并行写代码 (委托 effective-python)
  |
[Phase 5] 质量检查与测试   --> 脚本验证 (零 token) + /simplify + /test-cases
  |
[Phase 6] 更新文档         --> /update-docs Skill
```

每个阶段结束时，使用 `AskUserQuestion` 与用户确认产出后再进入下一阶段。

## Quick Reference

### 场景决策

| 场景 | 行动 |
|------|------|
| 新功能 | Phase 1→6 全流程，Phase 2 识别新实体，Phase 3 设计新接口 |
| 功能增强 | Phase 1→6，Phase 2 扩展现有实体，Phase 3 扩展接口方法 |
| Bug 修复 | Phase 1 澄清行为，Phase 2 定位错误实体，通常不涉及接口变更 |
| 架构重构 | Phase 1 确认约束，Phase 2 重新审视聚合边界，Phase 3 重新设计接口 |
| 性能优化 | Phase 1 确认目标，Phase 2 识别瓶颈实体，可能新增缓存/批量接口 |
| 代码质量优化 | 直接使用 effective-python skill，无需走全流程 |

### 各阶段执行方式

| Phase | 脚本 (零 token) | LLM (消耗 token) | Skill |
|-------|----------------|-------------------|-------|
| 1. 需求分析 | — | 识别类型 + 澄清需求 | — |
| 2. DDD 拆分 | `analyze-domain.py` | 设计新模型 | — |
| 3. 接口设计 | — | 设计接口 + DI | — |
| 4. 并行实现 | PostToolUse hook | Agent 写代码 | **effective-python** |
| 5. 质量检查 | `quality-check.sh` + `verify-architecture.py` | /simplify + /test-cases | simplify, test-cases |
| 6. 更新文档 | — | — | update-docs |

### 领域概念 → 代码位置映射

| 领域概念 | 代码位置 |
|---------|---------|
| 实体 | `core/entities.py` |
| 值对象 | `core/entities.py` |
| 聚合根 | `core/entities.py` |
| 领域服务接口 | `core/converter.py` |
| 领域异常 | `core/exceptions.py` |
| 领域服务实现 | `infrastructure/` |
| 配置 | `infrastructure/config.py` |

## Phase 摘要

详细步骤见 **[references/phases.md](references/phases.md)**。

### Phase 1: 需求分析与细化
识别需求类型（新功能/增强/Bug修复/重构/优化），澄清关键问题，产出结构化需求规格。

### Phase 2: DDD 领域拆分
运行 `scripts/analyze-domain.py` 分析现有领域（零 token），LLM 设计新领域模型。详见 [references/ddd-patterns.md](references/ddd-patterns.md)。

### Phase 3: 接口设计 (Clean Architecture)
设计核心接口（端口）、依赖注入点、基础设施实现契约。详见 [references/clean-architecture.md](references/clean-architecture.md)。

### Phase 4: 并行实现
先写 Core 层（无依赖），再用 Agent 并行写 Infrastructure + Interfaces + Tests。**代码实现委托 effective-python skill**，确保代码风格和模式符合最佳实践。PostToolUse hook 自动格式化。详见 [references/workflow-config.md](references/workflow-config.md)。

### Phase 5: 质量检查与测试
脚本优先：`scripts/quality-check.sh` + `scripts/verify-architecture.py`。通过后 `/simplify` + `/test-cases`。

### Phase 6: 更新文档
使用 `/update-docs` 更新 CLAUDE.md 和项目文档。

## Anti-Patterns → Correct Patterns

| ❌ Anti-Pattern | ✅ Correct Pattern |
|----------------|-------------------|
| 贫血模型：实体只有属性没有行为 | 富领域模型：把行为放在实体上，实体控制状态转换 |
| 聚合过大：一个聚合包含太多实体 | 聚合应尽量小，只包含需要一致性保证的实体 |
| 忽略值对象：所有东西都用 Entity | 能用值对象就用值对象（`frozen=True` dataclass） |
| 领域服务滥用：所有逻辑都放服务中 | 只在跨实体逻辑时用领域服务，单实体行为放实体上 |
| core 依赖 infrastructure | core 只定义抽象接口，infrastructure 实现 core 接口 |
| interfaces 直接 import infrastructure | 通过 DI 获取抽象接口，不直接依赖具体实现 |
| 异常类遮蔽内置名 | 使用描述性前缀避免遮蔽（如 `InputFileNotFoundError`） |
| LLM 做脚本能做的事 | 脚本优先：格式化、lint、类型检查、架构验证用脚本 |
| 架构师直接写实现代码 | 委托 effective-python skill 处理代码级细节 |

## Verification Checklist

完成开发后，验证：

- [ ] 需求规格已写入 `plans/` 并经用户确认
- [ ] 领域模型已识别（实体、值对象、聚合根、领域服务）
- [ ] 核心接口使用 `ABC` + `abstractmethod`，方法使用领域语言
- [ ] `core/` 不依赖 `infrastructure/` 或 `interfaces/`（`verify-architecture.py` 通过）
- [ ] `interfaces/` 只依赖 `core/`，通过 DI 获取 infrastructure 实现
- [ ] 代码实现遵循 effective-python skill 的模式和质量标准
- [ ] `quality-check.sh` 全部通过
- [ ] 测试覆盖关键路径
- [ ] 文档已更新（CLAUDE.md + 项目文档）

## Reference Files

### References (详细文档 — 按需加载)
- `references/phases.md` — Phase 1-6 的详细步骤、模板和产出格式
- `references/templates.md` — 需求规格模板、领域模型模板
- `references/ddd-patterns.md` — DDD 战术模式参考
- `references/clean-architecture.md` — Clean Architecture 参考指南
- `references/workflow-config.md` — 工作流配置和 PostToolUse Hook

### Scripts (零 token 工具)
- `scripts/analyze-domain.py` — AST 分析现有领域模型
- `scripts/quality-check.sh` — 自动运行 ruff/pyright/pytest
- `scripts/verify-architecture.py` — AST 验证依赖方向