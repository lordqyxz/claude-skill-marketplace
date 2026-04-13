# Classes

> Dataclasses, properties, inheritance, memory optimization.

## Dataclasses

```python
from dataclasses import dataclass, field

# ✅ Basic
@dataclass
class Config:
    name: str
    timeout: int = 30

# ✅ With mutable default
@dataclass
class User:
    name: str
    tags: list[str] = field(default_factory=list)

# ✅ Immutable (frozen)
@dataclass(frozen=True)
class TaskId:
    value: str

# ✅ Comparable
@dataclass(order=True)
class Priority:
    value: int

# ✅ With validation
@dataclass
class Point:
    x: float
    y: float

    def __post_init__(self):
        if self.x < 0 or self.y < 0:
            raise ValueError("Coordinates must be positive")
```

## Properties

```python
class Circle:
    def __init__(self, radius: float):
        self._radius = radius

    @property
    def radius(self) -> float:
        return self._radius

    @radius.setter
    def radius(self, value: float) -> None:
        if value <= 0:
            raise ValueError("Radius must be positive")
        self._radius = value

    @property
    def area(self) -> float:
        """Computed property - no setter needed."""
        return 3.14159 * self._radius ** 2
```

## Inheritance Patterns

```python
# ✅ Composition over inheritance
class Processor:
    def __init__(self, validator: Validator, transformer: Transformer):
        self._validator = validator
        self._transformer = transformer

# ✅ Mixin for reusable behavior
class LoggingMixin:
    def log(self, message: str) -> None:
        print(f"[{self.__class__.__name__}] {message}")

class Service(LoggingMixin):
    def process(self) -> None:
        self.log("Processing...")

# ✅ super() for MRO
class Child(BaseService):
    def __init__(self, name: str, timeout: int):
        super().__init__(name)
        self.timeout = timeout
```

## Memory Optimization

```python
# ✅ __slots__ for many instances
class Point:
    __slots__ = ("x", "y")

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

# Memory: ~40% reduction vs regular class
# Trade-off: No __dict__, can't add attributes dynamically
```
