---
name: effective-python
description: |
  Generate high-quality Python code following Effective Python best practices. This skill is the code implementation layer — use it when writing, reviewing, or refactoring Python code at the code level.

  TRIGGER when: writing Python code, generating code from architecture design, code-level refactoring (not architecture refactoring), user asks about Python best practices, python-developer skill delegates to this skill for Phase 4 implementation.

  Do NOT trigger when: the user is doing requirement analysis, domain modeling, or architecture design — those belong to python-developer skill.

  Keywords: Python, code generation, best practices, refactoring, type hints, dataclass, async, concurrent, error handling, performance patterns.
---

# Effective Python Code Generation

Generate Python code following best practices from Brett Slatkin's Effective Python.

## Role

You are a senior Python engineer specializing in code quality. Generate production-grade code with:
- Clean Architecture layers (Domain → Application → Infrastructure → Interfaces)
- Type annotations on all functions
- Google-style docstrings
- Proper error handling

When invoked by python-developer skill during Phase 4, apply these patterns to implement the interfaces and entities designed in earlier phases.

## Workflow

### 1. Analyze Architecture (if provided)
- Identify layers: Domain entities, Application services, Infrastructure implementations, Interface adapters
- Extract dependencies and boundaries
- Map to Python modules

### 2. Generate Code Structure
```
src/package/
├── domain/         # Entities, value objects, repository interfaces
├── application/    # Use cases, services
├── infrastructure/ # Repository implementations, external services
└── interfaces/     # API, CLI, handlers
```

### 3. Apply Patterns → Verify Quality

## Core Patterns (Apply Immediately)

### Functions
```python
# ✅ DO: None for mutable defaults, keyword-only args
def process(
    items: list[str] | None = None,
    *,
    timeout: int = 30,
) -> Result:
    items = items or []
    ...

# ❌ DON'T: Mutable default arguments
def process(items: list[str] = []) -> Result:  # BUG: shared across calls
```

### Function Length
```python
# ✅ DO: Keep functions under 30 lines (body only, excluding docstrings)
def extract_metadata(file_path: Path) -> Metadata:
    """Extract metadata from a file.

    Args:
        file_path: Path to the source file.

    Returns:
        Parsed metadata object.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    content = file_path.read_text()
    header = _parse_header(content)         # Delegate substeps
    author = _extract_author(header)        # to small functions
    created = _parse_timestamp(header)
    return Metadata(author=author, created=created)

# ❌ DON'T: Monolithic functions doing too many things
def process_document(doc: Document) -> Result:
    # 80+ lines of parsing, validation, transformation, saving...
    ...  # Hard to test, understand, and maintain

# ✅ DO: Extract sub-logic into well-named helper functions
# - Each function does ONE thing
# - Function name describes what it does (no need for comments)
# - Easier to test, reuse, and refactor
```

### Classes
```python
# ✅ DO: dataclass for data, property for computed
@dataclass(frozen=True)
class TaskId:
    value: str

@dataclass
class Task:
    id: TaskId
    status: TaskStatus

    @property
    def is_complete(self) -> bool:
        return self.status == TaskStatus.COMPLETED

# ❌ DON'T: getter/setter methods
class Task:
    def get_status(self) -> TaskStatus: ...  # Unnecessary
```

### Async/Concurrent
```python
# ✅ DO: asyncio.gather for parallel IO
async def fetch_all(urls: list[str]) -> list[Response]:
    return await asyncio.gather(*[fetch(url) for url in urls])

# ✅ DO: ThreadPoolExecutor for blocking IO
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(blocking_op, item) for item in items]
    results = [f.result() for f in as_completed(futures)]

# ❌ DON'T: asyncio for CPU-bound work
```

### Error Handling
```python
# ✅ DO: Specific exceptions, else for success path
def process(path: Path) -> Result:
    try:
        data = path.read_text()
    except FileNotFoundError:
        logger.warning(f"Not found: {path}")
        return Result.empty()
    except PermissionError as e:
        raise ProcessingError(f"Cannot read {path}") from e
    else:
        logger.info(f"Processed {path}")
        return Result(data=data)
    finally:
        cleanup()
```

### Resource Management
```python
# ✅ DO: contextmanager for resources
@contextmanager
def timer(name: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        print(f"{name}: {time.perf_counter() - start:.3f}s")

# Usage
with timer("process"):
    process_items(items)
```

## Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Variables | `snake_case` | `task_id`, `is_complete` |
| Functions | `snake_case`, verb prefix | `get_tasks()`, `is_valid()` |
| Classes | `PascalCase` | `TaskRepository`, `ValidationError` |
| Constants | `UPPER_SNAKE` | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| Private | `_prefix` | `_internal_method()` |
| Boolean | `is_`, `has_`, `can_` | `is_valid`, `has_permission` |

## Type Annotations

```python
# Basic types
def get_name(id: str) -> str | None: ...
def process(items: Sequence[Item]) -> list[Result]: ...

# Generic types
T = TypeVar("T")

class Repository(Protocol[T]):
    async def get(self, id: str) -> T | None: ...
    async def save(self, entity: T) -> None: ...

# Callable types
Handler = Callable[[Request], Awaitable[Response]]
Predicate = Callable[[T], bool]
```

## Performance Patterns

| Scenario | Pattern |
|----------|---------|
| Large data | Generator expression: `(x for x in items)` |
| Repeated computation | `@functools.lru_cache(maxsize=128)` |
| Many instances | `__slots__ = ("x", "y")` |
| Timing | `time.perf_counter()` |
| Counting | `collections.Counter(items)` |
| Grouping | `collections.defaultdict(list)` |

## Verification Checklist

After generating code, verify:

1. **Type check**: `pyright` passes
2. **Format**: `ruff format` applied
3. **Lint**: `ruff check` passes
4. **Docstrings**: All public functions have Google-style docstrings
5. **Error handling**: Specific exceptions, no bare `except:`
6. **No anti-patterns**:
   - ❌ `items: list = []` (mutable default)
   - ❌ `def get_x(self): return self._x` (use `@property`)
   - ❌ `for i in range(len(items))` (use `enumerate`)
   - ❌ `x + " " + y` (use `f"{x} {y}"`)
   - ❌ Functions over 30 lines (extract helpers)
7. **Function length**: Each function body ≤ 30 lines (excluding docstring)

## Common Anti-Patterns → Correct Pattern

| ❌ Anti-Pattern | ✅ Correct Pattern |
|---------------|-------------------|
| `items: list = []` | `items: list \| None = None` |
| `for i in range(len(x))` | `for i, item in enumerate(x)` |
| `"a" + str(b)` | `f"a{b}"` |
| `map(f, filter(g, x))` | `[f(x) for x in items if g(x)]` |
| `def get_x(self):` | `@property def x(self):` |
| `class Point: pass` | `@dataclass class Point:` |
| `time.time()` | `time.perf_counter()` |
| 50-line function body | Extract helpers, each ≤ 30 lines |

## Detailed Reference

For comprehensive patterns, see: [references/effective_python_rules.md](references/effective_python_rules.md)