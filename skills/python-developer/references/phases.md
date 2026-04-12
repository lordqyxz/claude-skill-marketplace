# Phase 详细步骤

各 Phase 的详细执行步骤、模板和产出格式。

## Table of Contents

- [Phase 1: 需求分析与细化](#phase-1-需求分析与细化)
- [Phase 2: DDD 领域拆分](#phase-2-ddd-领域拆分)
- [Phase 3: 接口设计 (Clean Architecture)](#phase-3-接口设计-clean-architecture)
- [Phase 4: 并行实现](#phase-4-并行实现)
- [Phase 5: 质量检查与测试](#phase-5-质量检查与测试)
- [Phase 6: 更新文档](#phase-6-更新文档)

---

## Phase 1: 需求分析与细化

> LLM 阶段 — 脚本无法理解自然语言需求

目标：将模糊的需求转化为清晰、可执行的需求规格。

### 步骤

1. **识别需求类型**

   需求通常属于以下类型之一：

   | 类型 | 特征 | 示例 |
   |------|------|------|
   | 新功能 | 添加全新的业务能力 | "添加 PDF 水印功能" |
   | 功能增强 | 扩展现有功能 | "支持批量转换时设置不同输出格式" |
   | Bug 修复 | 修复已有功能的异常行为 | "大文件转换超时" |
   | 重构 | 改善内部结构，不改变外部行为 | "将 Worker Pool 重构为插件式架构" |
   | 性能优化 | 提升性能指标 | "减少转换等待时间" |

   不同类型的需求，后续分析的侧重点不同。例如新功能需要识别新实体，Bug 修复通常不涉及接口变更。

2. **需求澄清**

   使用 `AskUserQuestion` 确认关键问题（根据需求类型选择重点）：

   **新功能/功能增强**：
   - 业务场景是什么？谁使用？解决什么问题？
   - 输入和输出分别是什么？
   - 与现有功能的关系？
   - 是否有特定的非功能要求（性能、安全、兼容性）？

   **Bug 修复**：
   - 预期行为 vs 实际行为？
   - 复现条件和频率？
   - 影响范围？

   **重构/性能优化**：
   - 当前痛点是什么？
   - 期望达到什么目标？
   - 有哪些约束（不能改变的外部接口）？

3. **产出：需求规格**

   将需求整理为结构化规格，写入计划文件（`plans/` 目录下）。模板见 [references/templates.md](templates.md)。

4. **与用户确认**

   展示需求规格，使用 `AskUserQuestion` 确认需求理解是否正确、验收标准是否完整。

---

## Phase 2: DDD 领域拆分

> 脚本 + LLM 阶段 — 脚本分析现有代码（零 token），LLM 设计新模型

目标：将需求转化为领域模型，识别核心概念和关系。

### 步骤

1. **脚本分析现有领域模型** (零 token)

   运行领域分析脚本，快速获取当前领域模型的全貌：

   ```bash
   python scripts/analyze-domain.py
   ```

   脚本输出包含：聚合根、值对象、领域服务接口的结构化报告。优势：毫秒级执行，零 token 消耗，完整报告。先看报告再决策，而不是让 LLM 逐个读文件。

2. **LLM 设计新领域模型**

   基于脚本输出的现有模型和 Phase 1 的需求规格，识别新/变更的领域概念：

   - **实体 (Entity)**：有唯一标识，生命周期跨越多个操作。例如 `TaskResult` 有 `task_id` 标识。
   - **值对象 (Value Object)**：无唯一标识，通过属性值定义相等性。例如 `TaskStatus` 是枚举值对象。
   - **聚合根 (Aggregate Root)**：一组相关实体的入口点，对外保证一致性边界。
   - **领域服务 (Domain Service)**：不属于任何单一实体的业务逻辑。

   详细的 DDD 模式参考见 [references/ddd-patterns.md](ddd-patterns.md)。

3. **绘制领域模型**

   在计划文件中记录领域模型。模板见 [references/templates.md](templates.md)。

4. **映射到代码结构**

   将领域模型映射到 `core/` 目录结构：

   ```markdown
   ### 代码结构映射

   src/[package]/core/
   +-- entities.py       # 实体和值对象
   +-- converter.py      # 领域服务接口
   +-- exceptions.py     # 领域异常
   ```

5. **与用户确认**

   使用 `AskUserQuestion` 确认领域概念识别是否准确、聚合边界是否合理。

---

## Phase 3: 接口设计 (Clean Architecture)

> LLM 阶段 — 需要设计决策，脚本无法替代

目标：基于领域模型设计核心接口，明确各层契约。

### Clean Architecture 分层

```
+-------------------------------------+
|         Interfaces (接口层)          |  CLI, HTTP API, GUI
|  依赖 core，不依赖 infrastructure    |
+-------------------------------------+
|           Core (核心层)              |  实体, 领域服务, 异常
|         无外部依赖                   |
+-------------------------------------+
|      Infrastructure (基础设施层)     |  数据库, 外部服务, 框架
|     实现 core 定义的接口              |
+-------------------------------------+

依赖方向: Interfaces -> Core <- Infrastructure
```

详细的 Clean Architecture 参考见 [references/clean-architecture.md](clean-architecture.md)。

### 步骤

1. **设计核心接口 (core/)**

   在 `core/` 中定义抽象接口（端口），这是依赖倒置的关键：

   ```python
   # core/converter.py - 领域服务接口
   from abc import ABC, abstractmethod

   class ConversionWorkerPool(ABC):
       """转换工作池接口 - 由 infrastructure 层实现"""

       @abstractmethod
       async def start(self) -> None: ...

       @abstractmethod
       async def submit(self, source: bytes, source_filename: str,
                        target_type: str, timeout: int | None = None) -> str: ...
   ```

   设计原则：
   - 接口方法使用领域语言，不暴露技术细节
   - 参数和返回值使用领域实体，不使用技术类型
   - 每个方法有明确的契约（前置条件、后置条件、异常）

2. **设计依赖注入点 (interfaces/)**

   在接口层定义依赖注入，确保接口层只依赖核心层抽象：

   ```python
   # interfaces/http/dependencies.py
   from ...core.converter import ConversionWorkerPool  # 依赖抽象

   def get_worker_pool() -> ConversionWorkerPool: ...
   ```

3. **设计基础设施实现 (infrastructure/)**

   确定基础设施需要实现的核心接口和配置：

   ```python
   # infrastructure/worker_pool.py
   class LibreOfficeWorkerPool(ConversionWorkerPool):
       """LibreOffice 实现 - 具体技术细节在这里"""
       ...
   ```

4. **产出：接口设计文档**

   在计划文件中记录接口设计（格式见 [references/clean-architecture.md](clean-architecture.md)）。

5. **与用户确认**

   使用 `AskUserQuestion` 确认接口划分是否合理、是否有遗漏。

---

## Phase 4: 并行实现

> 脚本格式化 + Agent 并行阶段

目标：接口确定后，各层代码并行编写，最大化效率。

### 并行策略

```
                    +-> Core 层实现 (entities.py, exceptions.py)
                    |   依赖: 无
                    |
接口设计确认 -------+-> Infrastructure 层实现
                    |   依赖: core 层接口
                    |
                    +-> Interfaces 层实现
                    |   依赖: core 层接口
                    |
                    +-> Tests 编写
                        依赖: core 层接口
```

**执行顺序**：
1. 先实现 Core 层（无依赖），写入 `entities.py`、`exceptions.py`、`converter.py`
2. 脚本自动格式化（PostToolUse hook，零 token）：`ruff format` + `ruff check --fix`
3. 使用 `Agent` 工具并行启动 Infrastructure 和 Interfaces 的实现
4. Tests 可以与 Infrastructure/Interfaces 并行编写（mock 核心接口）

### PostToolUse Hook 自动格式化

每次 Write/Edit Python 文件后，hook 自动运行。配置详情见 [references/workflow-config.md](workflow-config.md)。

如果项目尚未配置，Phase 4 开始前应先设置。

### 实现规范

**文件组织**：

```
src/[package]/
+-- core/
|   +-- __init__.py        # 导出领域公共 API
|   +-- entities.py        # 实体和值对象
|   +-- converter.py       # 领域服务接口 (ABC)
|   +-- exceptions.py      # 领域异常
|
+-- infrastructure/
|   +-- __init__.py        # 导出基础设施公共 API
|   +-- config.py          # pydantic-settings 配置
|   +-- [impl].py          # 核心接口的具体实现
|
+-- interfaces/
    +-- cli/
    |   +-- main.py        # CLI 入口
    +-- http/
        +-- app.py          # FastAPI 应用
        +-- routes.py       # 路由定义
        +-- dependencies.py # DI 配置
```

**代码风格**：委托 effective-python skill。关键约束：
- 实体使用 `@dataclass`，值对象使用 `@dataclass(frozen=True)`
- 领域接口使用 `ABC` + `abstractmethod`
- 异常类以 `Error` 结尾，避免遮蔽内置异常
- 接口层只依赖 `core`，通过 DI 获取 `infrastructure` 实现

### 并行实现执行

1. **Core 层**：直接写入，无需并行
2. **Infrastructure + Interfaces + Tests**：用 `Agent` 工具并行启动

   每个 agent prompt 包含：
   - 要实现的接口定义（从 Phase 3 产出）
   - 遵循 effective-python skill 的代码风格和模式
   - 文件组织规范

### 实现完成检查

每个文件实现后，确保：
- `__init__.py` 正确导出公共 API
- 导入路径正确（相对导入 vs 绝对导入）
- 代码风格遵循 effective-python skill

---

## Phase 5: 质量检查与测试

> 脚本优先阶段 — 大部分检查零 token

目标：验证实现的正确性和质量。

### 步骤

1. **脚本运行质量检查** (零 token)

   ```bash
   bash scripts/quality-check.sh
   ```

   脚本自动执行：
   - `ruff format --check` — 格式化检查
   - `ruff check` — Lint 检查
   - `pyright` — 类型检查
   - `pytest --cov` — 测试 + 覆盖率

   输出量化报告：格式问题数、Lint 问题数、类型错误数、测试覆盖率。

2. **脚本验证架构一致性** (零 token)

   ```bash
   python scripts/verify-architecture.py
   ```

   脚本使用 AST 分析验证依赖方向：
   - `core/` 不依赖 `infrastructure/` 或 `interfaces/`
   - `interfaces/` 只依赖 `core/`（不直接依赖 `infrastructure/`）
   - `infrastructure/` 依赖 `core/`（实现核心接口）

   如果发现违反，输出具体违反位置，需要重构使依赖方向正确。

3. **LLM 辅助检查** (需要 LLM)

   如果脚本检查通过，运行 LLM 辅助的质量提升：

   - 使用 `/simplify` Skill 审查代码质量
   - 使用 `/test-cases` Skill 生成补充测试

   这些 Skill 会在脚本验证的基础上，进一步审查代码重用性、效率、测试覆盖度。

4. **问题修复**

   如果检查发现问题，修复后重新运行脚本验证。

### 质量检查执行策略

```
脚本检查 (零 token)
  |
  +-- 通过 → 运行 /simplify + /test-cases (LLM 辅助)
  |
  +-- 失败 → 修复问题 → 重新运行脚本 → 直到通过
```

先确保脚本层面的基本质量，再让 LLM 做更深层的审查。避免 LLM 浪费 token 在格式/lint 这种脚本能处理的问题上。

---

## Phase 6: 更新文档

> Skill 阶段 — 使用 /update-docs Skill

目标：确保文档与代码保持同步。

### 步骤

1. **使用 /update-docs Skill 更新 CLAUDE.md**

   在 CLAUDE.md 中更新：
   - Architecture 部分（如有新增层或模块）
   - Important Files 部分（新增文件）
   - Key Design Decisions（新增设计决策）
   - Recent Changes（记录本次变更）

2. **更新项目文档**

   根据变更类型更新 `docs/` 目录下的相关文档：
   - `docs/API.md` - 新增或变更的 API 端点
   - `docs/CONFIGURATION.md` - 新增配置项
   - `docs/DEVELOPMENT.md` - 开发环境变化

3. **更新 `__init__.py` 导出**

   确保 `__all__` 列表与实际公共 API 一致。