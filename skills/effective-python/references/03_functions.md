# Functions

> Parameters, type annotations, function length, decorators, context managers.

## Parameters

```python
# ✅ Positional + keyword-only
def process(
    data: bytes,           # Required positional
    *,
    timeout: int = 30,     # Keyword-only
    retry: int = 3,
) -> Result:
    ...

# ✅ Optional mutable
def append_items(items: list[str] | None = None) -> list[str]:
    items = items or []
    items.append("new")
    return items

# ✅ Variable arguments
def log(level: str, *messages: str, **context: Any) -> None:
    print(f"[{level}]", *messages, context)

# ❌ NEVER: Mutable default
def process(items: list = []) -> Result:  # BUG!
```

## Type Annotations

```python
from typing import TypeAlias, TypeVar, Generic, Protocol, Callable

# Type aliases
TaskId: TypeAlias = str
JsonDict: TypeAlias = dict[str, Any]

# Generic types
T = TypeVar("T")
U = TypeVar("U")

class Stack(Generic[T]):
    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

# Protocol (structural typing)
class Validator(Protocol):
    def validate(self, data: bytes) -> bool: ...

# Callable
Handler = Callable[[Request], Awaitable[Response]]
Predicate = Callable[[T], bool]
```

## Function Length (≤ 30 lines body)

Keep function bodies under 30 lines (excluding docstrings). Long functions indicate mixed responsibilities — extract helpers.

```python
# ✅ DO: Short, focused functions — each does ONE thing
def extract_metadata(file_path: Path) -> Metadata:
    """Extract metadata from a file."""
    content = file_path.read_text()
    header = _parse_header(content)
    author = _extract_author(header)
    created = _parse_timestamp(header)
    return Metadata(author=author, created=created)

def _parse_header(content: str) -> dict[str, str]:
    """Parse the header section from file content."""
    lines = content.split("\n", maxsplit=10)
    return dict(line.split(":", 1) for line in lines if ":" in line)

# ❌ DON'T: Monolithic function doing everything
def process_document(doc: Document) -> Result:
    # 80+ lines of parsing, validation, transformation, saving...
    # Hard to test, understand, and maintain
    ...

# Guidelines:
# - ≤ 10 lines: ideal — one clear responsibility
# - 10-20 lines: acceptable — still readable
# - 20-30 lines: borderline — consider extracting helpers
# - > 30 lines: refactor — split into smaller functions
# - Exceptions: dispatch tables, data-driven logic (match/case, dict of handlers)
```

## Decorators

```python
import functools

# ✅ Preserve metadata
def trace(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

# ✅ Cache computation
@functools.lru_cache(maxsize=128)
def fibonacci(n: int) -> int:
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# Clear cache
fibonacci.cache_clear()
```

## Context Managers

```python
from contextlib import contextmanager, suppress, redirect_stdout
import io

# ✅ Custom context manager
@contextmanager
def timer(name: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        print(f"{name}: {time.perf_counter() - start:.3f}s")

# ✅ Suppress exceptions
with suppress(FileNotFoundError):
    os.remove("temp.txt")

# ✅ Capture output
output = io.StringIO()
with redirect_stdout(output):
    print("Hello")
result = output.getvalue()
```
