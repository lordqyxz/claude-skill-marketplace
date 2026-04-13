---
name: python-code
description: Write, refactor, and debug Python code following Pythonic best practices from the official Python style guide, Effective Python, and Fluent Python. Use this skill whenever the user writes, reviews, refactors, or debugs Python code, asks about Python patterns, idioms, or style, mentions writing a script/module/package in Python, or requests code that is "Pythonic." Applies to all Python 3.10+ code.
---

# Python Code Skill

Write Python code the way experienced Pythonistas write it — idiomatic, clear, and grounded in the principles from Python's official docs, *Effective Python* (Brett Slatkin), and *Fluent Python* (Luciano Ramalho).

## Why this skill exists

Python is deceptively simple. Code that *runs* isn't the same as code that's *Pythonic*. The difference shows up in readability, maintainability, and how well code plays with the rest of the ecosystem. This skill internalizes the accumulated wisdom from the language's core documentation and the two most respected Python methodology books, so every piece of Python code you write benefits from those insights without you having to look them up.

## Core Principles

These principles guide every line of Python you write. When trade-offs arise, refer back to these.

### 1. Readability counts — it's the #1 priority

Code is read far more often than it's written. Optimize for the reader, not the writer. This means:
- Obvious over clever. A list comprehension that fits one line is great; a nested comprehension that requires a whiteboard to unpack is not.
- Naming matters. `users_by_region` beats `d` or `grp`. If you need a comment to explain what a variable holds, the name is wrong.
- Prefer flat structure over deep nesting. Guard clauses (early return) keep indentation shallow and logic linear.

### 2. Use Python's power — don't fight it

Python has rich built-in types and protocols. Leverage them instead of reinventing:
- Use `collections` (`defaultdict`, `Counter`, `namedtuple`, `dataclasses`) instead of manual dict tricks.
- Use comprehensions and generator expressions instead of manual loops. List comprehensions are more readable than `map`+`lambda`, but `map` is fine when you already have a callable (`map(str, numbers)` beats `[str(n) for n in numbers]`).
- Use `yield` and generator functions for lazy pipelines — process data one item at a time without loading everything into memory. `yield from` delegates to sub-generators. `itertools` (`chain`, `islice`, `groupby`, `tee`) is the stdlib toolkit for building iterator pipelines.
- Use context managers (`with`) for resource management — files, locks, connections.
- Use the `pathlib` module instead of `os.path` for filesystem operations.
- Use f-strings instead of `.format()` or `%` formatting.
- Use `match`/`case` (3.10+) for destructuring structured data and replacing deep if/elif chains — it's cleaner than isinstance checks for complex branching.

### 3. Functions are the unit of composition

Small, focused functions with clear input/output contracts beat monolithic blocks:
- Each function does one thing. If you're writing a docstring and need "and" to list what it does, split it.
- Return values are better than mutating arguments. Mutating arguments creates hidden coupling that's hard to debug.
- Use type annotations. They communicate intent, enable static analysis, and cost nothing at runtime. `def search(needle: str, haystack: list[str]) -> int:` is self-documenting.
- **Separate I/O from logic.** Functions that mix file reads, network calls, or database queries with business logic are hard to test and brittle to refactor. Keep pure-data functions (take data in, return data out) separate from I/O adapters (read file, write result). This way the core logic can be tested without mocking filesystem or network, and the I/O layer can be swapped (e.g., from local files to S3) without touching business rules.
- **Choose the right callable form.** Prefer closures for simple state capture (a counter, a callback with context) — they're lighter than a class. Use `@dataclass` or a class only when you need multiple methods or a complex interface. A `def make_counter(start=0)` returning an inner function is simpler than a `Counter` class with `__call__`.
- **Keep function bodies under 30 lines** (excluding docstrings). Long functions indicate mixed responsibilities — extract helpers. Guidelines: ≤ 10 lines ideal, 10-20 acceptable, 20-30 borderline, > 30 refactor. Exceptions: dispatch tables, data-driven logic (match/case, dict of handlers).

### 4. Classes when you need state; functions when you don't

Don't reach for a class just because Java would. Functions and simple data structures cover most needs:
- If it's just data, use a `dataclass` or `NamedTuple`.
- If it has behavior and state, a class makes sense. Keep inheritance shallow — composition over inheritance.
- If you need a class, implement dunder methods so objects behave like native Python objects. The minimum depends on the class's role:
  - **All classes**: `__repr__` — so `repr(obj)` is useful in debugging and logging.
  - **Data-like classes**: `__eq__` and `__hash__` (if immutable) — so they work in sets/dicts.
  - **Container-like classes** (hold items, support lookup): `__len__`, `__contains__`, `__getitem__` — so `len(cache)`, `key in cache`, and `cache[key]` work. Without these, users must remember custom method names like `size()`, `get()` — a maintenance burden and a departure from Python conventions.
  - **Callable objects**: `__call__` — when configuration + behavior makes sense.

### 5. Handle errors explicitly, fail fast

- Raise specific exceptions (`ValueError`, `KeyError`, custom subclasses) — never bare `except:`.
- Use `try/except/else/finally` fully. The `else` clause runs when no exception occurred, which is clearer than putting success logic inside the `try`.
- Validate inputs at system boundaries (public API, user input). Trust internal callers — don't sprinkle validation everywhere.
- **Invalid input should raise, not silently adapt.** When a caller passes `ttl=-5`, raise `ValueError("ttl must be positive, got -5")` — don't silently treat it as "expire immediately." Silently reinterpreting invalid input hides bugs in the caller's code and makes diagnosing issues much harder. The exception message should include the actual value received so the caller can see what went wrong without adding print statements.

### 6. Concurrency and async with care

- Use `asyncio` for I/O-bound work, `concurrent.futures` for CPU-bound work.
- Prefer `asyncio.TaskGroup` (3.11+) over manual task creation — automatic cleanup and error propagation.
- Never mix sync and async code casually. If a function is async, everything it calls should be async or offloaded via `run_in_executor`.

## Code Style Rules

Follow PEP 8 as baseline, but go beyond it:

- **Line length**: 88 (Black default). Readability over arbitrary 80-char limits.
- **Imports**: `stdlib → third-party → local`, each group separated by a blank line. Use `from x import y` for specific names, `import x` for module-level access.
- **String quotes**: Consistent within a file. Don't mix without reason.
- **Trailing commas**: In multi-line collections, always. Makes diffs cleaner.
- **Type annotations**: All function signatures. Use `from __future__ import annotations` for forward references.
- **Naming conventions**:

| Element | Convention | Example |
|---------|------------|---------|
| Variables | `snake_case` | `task_id`, `is_complete` |
| Functions | `snake_case`, verb prefix | `get_tasks()`, `is_valid()` |
| Classes | `PascalCase` | `TaskRepository`, `ValidationError` |
| Constants | `UPPER_SNAKE` | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| Private | `_prefix` | `_internal_method()` |
| Boolean | `is_`, `has_`, `can_` | `is_valid`, `has_permission` |

- **Docstrings**: All public functions have Google-style docstrings.

## Patterns to Prefer

| Situation | Prefer | Avoid |
|-----------|--------|-------|
| Empty dict/list default param | `None` default + `if x is None: x = {}` | Mutable default `def f(x={})` |
| Simple data container | `@dataclass` or `NamedTuple` | Manual `__init__` |
| File paths | `pathlib.Path` | `os.path` string manipulation |
| Counting | `Counter` | `dict` with `if key in d` |
| Grouping | `defaultdict(list)` | `if key not in d: d[key] = []` |
| Iteration with index | `enumerate()` | `range(len())` |
| Parallel iteration | `zip()` | Index-based access |
| Conditional expression | `x if cond else y` | Multi-line `if/else` for simple cases |
| String building | `"".join(parts)` | `+=` in a loop |
| Resource cleanup | `with` statement | Manual `close()` calls |
| Attribute access with default | `getattr(obj, key, default)` | `try/except AttributeError` for simple cases |
| Dictionary merging (3.9+) | `d1 \| d2` | `d1.update(d2)` for immutable merging |
| Container class interface | `__len__`, `__contains__`, `__getitem__` | Custom `size()`, `has()`, `get_by_key()` methods |
| Structured data (evolving schema) | `@dataclass` with named fields | Tuple unpacking `value, ts = entry` |
| Business logic | Pure function taking/returning data | Function mixing I/O + computation |
| State capture (simple) | Closure with `nonlocal` | Full class for a counter/callback |
| Lazy data pipeline | Generator function with `yield` | Loading all data into a list |
| Operator overloading | `__add__` + `__radd__` + `__iadd__` | Only `__add__` (breaks `1 + obj`) |
| Structural branching (3.10+) | `match`/`case` with destructuring | Deep `isinstance` + `if/elif` chains |
| Parallel IO | `asyncio.gather` | Sequential awaits |
| Blocking IO | `ThreadPoolExecutor` | asyncio for CPU-bound work |
| High-precision timing | `time.perf_counter()` | `time.time()` |
| Repeated computation | `@functools.lru_cache` | Manual memoization |
| Many instances | `__slots__` | Regular `__dict__` class |
| Context manager | `@contextmanager` + `with` | Manual `try/finally` cleanup |

## Common Pitfalls to Avoid

These come from *Effective Python* and *Fluent Python* — each one has burned real projects:

1. **Mutable default arguments**: `def f(items=[]):` — the list persists across calls. Use `None` and create a new list inside the function.
2. **Closures over loop variables**: `lambda: i` in a loop captures the variable, not the value. Use `lambda i=i: i` or `functools.partial`.
3. **`is` for value comparison**: `is` checks identity, not equality. `x is None` is correct; `x is 0` or `x is []` is a bug.
4. **Star imports in production code**: `from module import *` pollutes the namespace and hides dependencies.
5. **Ignoring `__hash__` when overriding `__eq__`**: Unhashable objects break sets and dict keys.
6. **Overusing `@property`**: Complex computation hidden behind property access is misleading. If it's expensive, make it a method.
7. **Subclassing built-in types incorrectly**: If you override `__setitem__`, you probably also need `__getitem__`, `__delitem__`, `update`, etc. Consider composition instead.
8. **Returning `True`/`False` from `__init__`**: `__init__` should return `None`. Raise exceptions on failure.
9. **Using tuples for evolving data structures**: `entry = (value, timestamp)` is fine for a one-off script, but if the structure might grow (add `created_at`, `hit_count`), every unpacking site breaks. Use `@dataclass` from the start — the cost is trivial, the maintainability gain is real.
10. **Coupling I/O with business logic**: A function that reads a file, parses it, and returns results cannot be unit-tested without filesystem mocking. Split into: `parse_data(text: str) -> Result` (testable) + `read_and_parse(path: Path) -> Result` (I/O adapter). The pure function is where bugs live; the I/O adapter is infrastructure.
11. **Missing reverse operators**: If you implement `__add__`, Python falls back to `__radd__` on the right operand when the left doesn't know how to handle it. Without `__radd__`, `1 + Money(5)` works but `Money(5) + 1` may not — a subtle asymmetry.
12. **`__bool__` vs `__len__` confusion**: If both are defined, `bool(obj)` uses `__bool__`; if only `__len__`, zero is falsy. Forgetting `__bool__` when you have `__len__` leads to surprises — an empty-yet-valid container evaluates as falsy.
13. **Forgetting `nonlocal` in closures**: A nested function that assigns to an outer variable needs `nonlocal x` — without it, the assignment creates a local variable that shadows the outer one, and the outer variable is never updated.
14. **`__slots__` blocks `weakref`**: Adding `__slots__` removes `__dict__` *and* `__weakref__` by default. If you need weak references to instances, explicitly add `__weakref__` to `__slots__`.

## Verification Checklist

After writing or refactoring code, verify:

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

## When to go deeper

This skill covers day-to-day Python writing. For specialized topics, read the relevant reference file:

- **`references/advanced-types.md`** — Protocol, TypeVar, generics, overloads, type narrowing
- **`references/async-patterns.md`** — Async services, TaskGroup, mixing sync/async
- **`references/data-model.md`** — Dunder methods, descriptors, custom containers
- **`references/testing.md`** — Pytest fixtures, mocking, test patterns
- **`references/class-metaprogramming.md`** — `__init_subclass__`, `match`/`case` pattern matching, `__class_getitem__`
- **`references/effective-python/`** — Chapter-by-chapter patterns from *Effective Python*: pythonic thinking, lists/dicts, functions, classes, concurrency, error handling, performance, standard library

These are loaded only when needed to keep context lean — the core principles above cover the vast majority of Python code you'll write.