# DDD 战术模式参考

## 核心概念

### 实体 (Entity)

有唯一标识符的对象，即使属性相同，标识不同就是不同实体。

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class TaskResult:
    """实体 - 有唯一 task_id 标识"""
    task_id: str                          # 唯一标识
    status: TaskStatus
    result: bytes | None = None
    created_at: datetime = field(default_factory=datetime.now)
```

识别标志：需要跨多个操作追踪其生命周期。如果一个对象只是临时传递数据，不需要追踪，那它可能是值对象。

### 值对象 (Value Object)

没有唯一标识，通过属性值定义相等性。值对象应该是不可变的。

```python
from dataclasses import dataclass
from enum import Enum

class TaskStatus(str, Enum):
    """值对象 - 枚举类型"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass(frozen=True)
class ConversionFormat:
    """值对象 - 不可变的格式对"""
    source: str
    target: str

    def __post_init__(self):
        if not self.source or not self.target:
            raise ValueError("Source and target must not be empty")
```

识别标志：只关心它是什么，不关心它是哪个。两个 `ConversionFormat("doc", "docx")` 是完全等价的。

### 聚合根 (Aggregate Root)

一组相关实体的入口点，对外保证一致性边界。

```python
@dataclass
class ConversionTask:
    """聚合根 - 任务的一致性边界"""
    task_id: str
    source_format: str
    target_format: str
    status: TaskStatus = TaskStatus.PENDING
    result: bytes | None = None

    def start(self) -> None:
        """开始执行 - 状态转换由聚合根控制"""
        if self.status != TaskStatus.PENDING:
            raise InvalidStateTransitionError(
                f"Cannot start task in {self.status} state"
            )
        self.status = TaskStatus.RUNNING

    def complete(self, result: bytes) -> None:
        """完成执行"""
        if self.status != TaskStatus.RUNNING:
            raise InvalidStateTransitionError(
                f"Cannot complete task in {self.status} state"
            )
        self.status = TaskStatus.COMPLETED
        self.result = result
```

识别标志：需要保证内部状态一致性的一组对象。外部不应该直接修改聚合内部实体的状态，必须通过聚合根操作。

### 领域服务 (Domain Service)

不属于任何单一实体的业务逻辑。

```python
from abc import ABC, abstractmethod

class ConversionWorkerPool(ABC):
    """领域服务接口 - 协调多个实体的业务逻辑"""
    @abstractmethod
    async def submit(self, source: bytes, source_filename: str,
                     target_type: str) -> str: ...
```

识别标志：操作涉及多个实体，或者不属于任何一个实体的职责。

### 领域事件 (Domain Event)

领域中发生的、有业务含义的事件。

```python
@dataclass(frozen=True)
class TaskCompleted:
    """领域事件 - 不可变"""
    task_id: str
    completed_at: datetime
    execution_time: float
```

识别标志：业务上需要知道"这件事发生了"的场景。通常用于解耦——发布者不需要知道谁会消费这个事件。

## 领域拆分流程

1. 从需求中提取**名词** → 候选实体/值对象
2. 判断是否有唯一标识需求 → 实体 vs 值对象
3. 找出需要一致性保证的实体组 → 聚合根
4. 识别跨实体的业务逻辑 → 领域服务
5. 识别状态变更通知需求 → 领域事件
6. 识别错误场景 → 领域异常

## 常见陷阱

1. **贫血模型**：实体只有属性没有行为，所有逻辑都在服务中。应该把行为放在实体上。
2. **聚合过大**：一个聚合包含太多实体，导致并发冲突。聚合应该尽量小。
3. **忽略值对象**：所有东西都用 Entity，导致概念模糊。能用值对象就用值对象。
4. **领域服务滥用**：所有逻辑都放在领域服务中，实体变成纯数据容器。