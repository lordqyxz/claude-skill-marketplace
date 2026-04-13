# Advanced Type System Patterns

Reference for Python's advanced type features — loaded when working with Protocol, generics, overloads, or type narrowing.

## Protocol — Structural Subtyping

Instead of inheritance-based subtyping, Python's `Protocol` defines interfaces by structure ("if it has these methods, it qualifies"):

```python
from typing import Protocol

class Closeable(Protocol):
    def close(self) -> None: ...

def cleanup(resource: Closeable) -> None:
    resource.close()  # Any object with close() works
```

Why: This is Python's philosophy — "duck typing, but type-safe." Prefer Protocol over ABC for interface definitions. ABCs force inheritance; Protocols accept any compatible object.

## TypeVar and Generics

Use `TypeVar` when a function's return type depends on its input type:

```python
from typing import TypeVar

T = TypeVar("T")

def first(items: list[T]) -> T:
    return items[0]
```

For constrained generics (only certain types allowed):

```python
from typing import TypeVar

Number = TypeVar("Number", int, float)

def add(a: Number, b: Number) -> Number:
    return a + b
```

### TypeVarTuple (3.11+)

For variadic generics (like array shapes):

```python
from typing import TypeVarTuple, Unpack

Dims = TypeVarTuple("Dims")

class Array(Generic[*Dims]):
    shape: tuple[*Dims]
```

## Overload — Multiple Signatures

When a function accepts different argument types and returns differently based on them:

```python
from typing import overload

@overload
def get(key: str) -> str: ...
@overload
def get(key: int) -> int: ...

def get(key: str | int) -> str | int:
    if isinstance(key, str):
        return key.upper()
    return key * 2
```

Why: type checkers understand each overload independently. Without `@overload`, they can only infer the union type, losing precision about which return type goes with which input.

## Type Narrowing

Python's type checkers (mypy, pyright) understand several narrowing patterns:

**`isinstance` checks** — the most reliable:
```python
def process(value: str | int) -> str:
    if isinstance(value, int):
        return str(value)  # Narrowed to int
    return value.upper()   # Narrowed to str
```

**`None` checks** — for Optional types:
```python
def greet(name: str | None) -> str:
    if name is not None:
        return f"Hello, {name}"  # str
    return "Hello, stranger"      # also str
```

**`type()` checks** — exact type match:
```python
if type(x) is list:
    # x is exactly list, not a subclass
```

**`in` checks** — narrowing with literal sets:
```python
def handle(mode: str) -> None:
    if mode in ("read", "write"):
        # mode is "read" | "write"
```

## TypeGuard and TypeIs

Custom type narrowing functions:

```python
from typing import TypeGuard

def is_str_list(val: list[object]) -> TypeGuard[list[str]]:
    return all(isinstance(x, str) for x in val)

if is_str_list(items):
    # items narrowed to list[str]
```

`TypeIs` (3.13+) is stricter — it also narrows the input type, not just the output. Prefer `TypeIs` when available.

## ParamSpec and Concatenate

For decorating callables while preserving their signature:

```python
from typing import ParamSpec, Concatenate, Callable

P = ParamSpec("P")
R = TypeVar("R")

def retry(
    func: Callable[P, R],
) -> Callable[P, R]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return func(*args, **kwargs)
    return wrapper
```

Why: Without `ParamSpec`, decorators lose the original function's signature — type checkers see `*args, **kwargs` instead of the real parameters.

## Annotated — Runtime Metadata on Types

```python
from typing import Annotated

UserId = Annotated[int, "must be positive"]

def lookup(id: UserId) -> User: ...
```

Pydantic uses this extensively for validation constraints:
```python
from typing import Annotated
from pydantic import AfterValidator

PositiveInt = Annotated[int, AfterValidator(lambda x: abs(x))]
```

## Common Advanced Pitfalls

1. **Generic class attributes**: Don't use `TypeVar` in class attribute defaults — each instance doesn't get its own type parameter.
2. **`ClassVar` for class-level attributes**: Without `ClassVar`, mypy thinks `count: int` belongs to each instance.
3. **`Final` for constants**: `x: Final = 10` tells type checkers this shouldn't be reassigned.
4. **`@override` (3.12+)**: Mark methods that override parent class methods — catch typos in method names at type-check time.