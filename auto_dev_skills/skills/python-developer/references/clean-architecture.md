# Clean Architecture 参考指南

## 核心原则

**依赖规则**：依赖关系只能从外层指向内层。内层（核心层）不知道外层的任何东西。

```
+-------------------------------------------+
|  Frameworks & Drivers (DB, Web, UI)       |  最外层
+-------------------------------------------+
              |
+-------------------------------------------+
|  Interface Adapters (Controllers, Gateways)|
+-------------------------------------------+
              |
+-------------------------------------------+
|  Application Business Rules (Use Cases)    |
+-------------------------------------------+
              |
+-------------------------------------------+
|  Enterprise Business Rules (Entities)      |  最内层
+-------------------------------------------+
```

## 在 Python 项目中的实现

### 三层架构映射

对于典型的 Python 项目，Clean Architecture 可以简化为三层：

```
Core (领域层)          - 实体、值对象、领域服务接口、领域异常
Infrastructure (基础设施层) - 数据库、外部 API、框架实现
Interfaces (接口层)     - CLI、HTTP API、GUI
```

### 依赖方向

```python
# 正确的依赖方向

# core/ 不依赖任何外部层
# core/entities.py
@dataclass
class TaskResult:
    task_id: str
    status: TaskStatus

# core/converter.py
class ConversionWorkerPool(ABC):
    @abstractmethod
    async def submit(self, ...) -> str: ...

# infrastructure/ 依赖 core（实现核心接口）
# infrastructure/worker_pool.py
class LibreOfficeWorkerPool(ConversionWorkerPool):  # 实现核心接口
    async def submit(self, ...) -> str:
        # 具体的 LibreOffice 实现
        ...

# interfaces/ 只依赖 core（不直接依赖 infrastructure）
# interfaces/http/dependencies.py
def get_worker_pool() -> ConversionWorkerPool:  # 返回抽象接口
    ...

# interfaces/http/routes.py
pool = get_worker_pool()  # 只知道抽象接口
task_id = await pool.submit(...)  # 调用抽象方法
```

```python
# 错误的依赖方向 - 需要重构

# core/ 依赖了 infrastructure
# core/entities.py
from ..infrastructure.config import Settings  # 违反！core 不应依赖 infrastructure

# interfaces/ 直接依赖 infrastructure
# interfaces/http/routes.py
from ...infrastructure.worker_pool import LibreOfficeWorkerPool  # 违反！
# 应该通过 DI 获取抽象接口
```

### 依赖注入模式

**构造函数注入**（推荐）：

```python
class ConversionRoutes:
    def __init__(self, worker_pool: ConversionWorkerPool):
        self._worker_pool = worker_pool  # 接受抽象接口
```

**FastAPI Depends 注入**：

```python
# interfaces/http/dependencies.py
def get_worker_pool() -> ConversionWorkerPool:
    """返回抽象接口，具体实现由 app lifespan 配置"""
    ...

# interfaces/http/routes.py
@router.post("/convert")
async def convert(
    pool: ConversionWorkerPool = Depends(get_worker_pool),  # 注入抽象
):
    task_id = await pool.submit(...)
```

## 端口与适配器 (Hexagonal Architecture)

Clean Architecture 的一个具体实现形式：

- **端口 (Port)**：核心层定义的抽象接口（如 `ConversionWorkerPool`）
- **适配器 (Adapter)**：基础设施层的具体实现（如 `LibreOfficeWorkerPool`）

```
核心层定义端口:          基础设施层提供适配器:
ConversionWorkerPool --> LibreOfficeWorkerPool
                    --> WpsOfficeWorkerPool
                    --> CloudServiceWorkerPool
```

这种设计让替换技术实现变得简单——只需编写新的适配器，核心逻辑和接口层不需要任何改动。

## 接口设计原则

1. **接口用领域语言**：方法名和参数应该反映业务含义，不是技术操作
2. **接口粒度适中**：不要把所有方法放在一个大接口中，按职责分离
3. **接口稳定性**：核心接口应该比实现更稳定，修改接口影响面大
4. **契约明确**：每个方法的前置条件、后置条件、异常都应明确

## 架构验证

检查依赖方向是否正确的方法：

1. `core/` 的 import 中不应出现 `infrastructure` 或 `interfaces`
2. `interfaces/` 的 import 中不应出现具体的 `infrastructure` 实现类
3. `infrastructure/` 可以 import `core` 的抽象接口和实体

可以通过 AST 分析脚本自动验证这些规则。