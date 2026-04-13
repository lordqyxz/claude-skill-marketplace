# Class Metaprogramming and Pattern Matching

Reference for advanced class design — loaded when using `__init_subclass__`, `match`/`case`, or custom class creation patterns.

## `__init_subclass__` — Register and Validate Subclasses

Run code when a class is subclassed — useful for plugin registries and automatic validation:

```python
class PluginBase:
    _registry: dict[str, type] = {}

    def __init_subclass__(cls, name: str | None = None, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        plugin_name = name or cls.__name__.lower()
        PluginBase._registry[plugin_name] = cls

class CSVLoader(PluginBase, name="csv"):
    ...

class JSONLoader(PluginBase, name="json"):
    ...

# PluginBase._registry == {"csv": CSVLoader, "json": JSONLoader}
```

Why: Eliminates manual registration code. New plugins register themselves just by subclassing. This is how many frameworks (SQLAlchemy, Django) discover extensions.

## `match`/`case` — Structural Pattern Matching (3.10+)

Replace deep `isinstance` + `if/elif` chains with declarative destructuring:

```python
def handle_command(cmd: Command) -> str:
    match cmd:
        case Quit():
            return "bye"
        case Load(path=p, format="csv"):
            return f"loading CSV from {p}"
        case Load(path=p):
            return f"loading from {p}"
        case Move(x=dx, y=dy) if dx == dy:
            return f"diagonal move {dx}"
        case Move(x=dx, y=dy):
            return f"move to ({dx}, {dy})"
        case _:
            raise ValueError(f"unknown command: {cmd!r}")
```

Key patterns:
- **Destructuring**: `case Point(x, y):` unpacks attributes
- **Guards**: `case ... if condition:` adds runtime checks
- **Literal matching**: `case 200:` matches exact values
- **OR patterns**: `case "yes" | "y" | "yeah":`
- **As patterns**: `case [first, *rest] as parts:` binds the whole match
- **Exhaustiveness**: `case _:` is the catch-all (like `else`)

When to use: When a function branches on the structure or type of an object — especially with nested data, multiple types, or complex isinstance chains. Not for simple two-branch conditionals.

## `__class_getitem__` — Support Generic Syntax

Make a class work with `Class[Type]` syntax:

```python
class Matrix:
    def __class_getitem__(cls, shape: tuple[int, ...]) -> type:
        # Enables Matrix[3, 4] syntax
        ...

def process(m: Matrix[3, 4]) -> None:
    ...
```

Why: Without this, `Matrix[3, 4]` raises `TypeError`. This is what makes `list[int]`, `dict[str, float]` work in type annotations — the builtin types implement `__class_getitem__`.

## Class Creation Hooks Priority

When building classes, these hooks run in order:

1. `__init_subclass__` — runs on the *parent* when a child is defined
2. `__set_name__` — runs on each descriptor when the owning class is created
3. `__init__` — runs when an *instance* is created

Use `__init_subclass__` for class-level concerns (registration, validation of class attributes). Use `__set_name__` for descriptor-level concerns (knowing the attribute name). Use `__init__` for instance-level concerns.