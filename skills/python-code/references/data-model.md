# Python Data Model Deep Dive

Reference for implementing dunder methods, descriptors, and custom containers — loaded when you're designing Python objects that integrate naturally with the language.

## The Data Model: Why It Matters

Python's data model (dunder methods) is how your objects speak the language. Objects that implement the right dunders work naturally with `len()`, `in`, `for`, `+`, comparison, and all the built-in functions. Users of your code don't need to memorize custom method names — they just use Python.

## Essential Dunder Methods

### Object representation

```python
class User:
    def __init__(self, name: str, uid: int) -> None:
        self.name = name
        self.uid = uid

    def __repr__(self) -> str:
        return f"User({self.name!r}, uid={self.uid})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return NotImplemented
        return self.uid == other.uid

    def __hash__(self) -> int:
        return hash(self.uid)
```

Why `NotImplemented` not `False`: Returning `NotImplemented` gives Python a chance to try the reversed operation (`other.__eq__(self)`). Returning `False` short-circuits this.

### Container protocol

```python
class DataTable:
    def __init__(self, columns: list[str], rows: list[list]):
        self._columns = columns
        self._rows = rows

    def __len__(self) -> int:
        return len(self._rows)

    def __getitem__(self, key: int | str) -> Any:
        if isinstance(key, str):
            idx = self._columns.index(key)
            return [row[idx] for row in self._rows]
        return self._rows[key]

    def __contains__(self, item: Any) -> bool:
        return any(item in row for row in self._rows)

    def __iter__(self) -> Iterator[list]:
        return iter(self._rows)
```

With just `__len__` and `__getitem__`, Python gives you iteration, `reversed()`, slicing (if `__getitem__` handles slices), and membership testing for free.

### Callable objects

```python
class Multiplier:
    def __init__(self, factor: float) -> None:
        self.factor = factor

    def __call__(self, x: float) -> float:
        return x * self.factor

double = Multiplier(2.0)
double(5)  # 10.0
```

Why over a plain function: When the callable needs configuration or state.

### Numeric protocol

```python
class Money:
    def __init__(self, amount: int, currency: str) -> None:
        self.amount = amount
        self.currency = currency

    def __add__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare {self.currency} and {other.currency}")
        return self.amount < other.amount
```

With `__lt__` and `__eq__`, `functools.total_ordering` fills in the rest (`<=`, `>`, `>=`).

## Descriptors

Descriptors control attribute access. A descriptor is any object with `__get__`, `__set__`, or `__delete__`:

```python
class Validated:
    def __init__(self, validator: Callable[[Any], None]):
        self.validator = validator

    def __set_name__(self, owner: type, name: str) -> None:
        self.private_name = f"_{name}"

    def __get__(self, obj: object, objtype: type | None = None) -> Any:
        if obj is None:
            return self
        return getattr(obj, self.private_name)

    def __set__(self, obj: object, value: Any) -> None:
        self.validator(value)
        setattr(obj, self.private_name, value)

class Person:
    age = Validated(lambda x: assert x >= 0, "Age must be non-negative")
```

**Data descriptor** (has `__set__`): Takes priority over instance `__dict__`. Use for computed/validated attributes.
**Non-data descriptor** (only `__get__`): Instance `__dict__` takes priority. Use for methods — this is how `self` binding works.

### `property` is a descriptor

```python
# These are equivalent:
class C:
    @property
    def x(self): return self._x

    @x.setter
    def x(self, value): self._x = value

# property() is just a built-in data descriptor factory
```

## `__slots__` — When to Use

`__slots__` saves memory by preventing per-instance `__dict__`:

```python
class Point:
    __slots__ = ("x", "y")

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
```

Use when: Creating millions of instances (data processing, game entities). The memory savings are significant (~40-50% per object).

Avoid when: You need dynamic attribute addition, or you're creating only a handful of objects. The rigidity isn't worth it.

## Context Managers

Two ways to create them:

### Class-based

```python
class DatabaseConnection:
    def __enter__(self) -> DatabaseConnection:
        self.conn = connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.conn.close()
        # Return None (or falsy) to propagate exceptions
        # Return True to suppress the exception
```

### `@contextmanager` — generator-based

```python
from contextlib import contextmanager

@contextmanager
def temp_directory():
    dir = Path(tempfile.mkdtemp())
    try:
        yield dir
    finally:
        shutil.rmtree(dir)
```

Prefer `@contextmanager` when setup/teardown is simple. Prefer class-based when the context object has its own methods.

## Data Model Pitfalls

1. **`__del__` is unreliable**: Python's GC doesn't guarantee when `__del__` runs. Use context managers for deterministic cleanup.
2. **`__hash__` must be consistent with `__eq__`**: Equal objects must have equal hashes. If you define `__eq__`, either define `__hash__` or set `__hash__ = None` to make the object unhashable.
3. **`__bool__` overrides `__len__` for truthiness**: If both are defined, `bool(obj)` uses `__bool__`.
4. **`__getattr__` vs `__getattribute__`**: `__getattr__` is called only when normal lookup fails. `__getattribute__` is called for *every* attribute access — use carefully, circular calls are easy.
5. **Mutating `__eq__` with `__iadd__`**: `+=` calls `__iadd__` if it exists, falling back to `__add__`. If you want in-place mutation, implement `__iadd__`; otherwise, `__add__` creates a new object.