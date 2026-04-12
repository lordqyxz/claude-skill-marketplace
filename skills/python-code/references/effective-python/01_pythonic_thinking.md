# Pythonic Thinking

> String formatting, iteration, walrus operator, control flow patterns.

## String Formatting

```python
# ✅ f-string (preferred)
message = f"Hello {name}, count: {count}"
value = f"{number:.2f}"

# ✅ Multiline
sql = f"""
    SELECT * FROM users
    WHERE id = {user_id}
"""

# ❌ Old styles (avoid)
message = "Hello %s" % name
message = "Hello {}".format(name)
```

## Iteration Patterns

```python
# ✅ enumerate with index
for i, item in enumerate(items, start=0):
    print(f"{i}: {item}")

# ✅ zip for parallel iteration
for name, score in zip(names, scores):
    print(f"{name}: {score}")

# ✅ zip_longest for unequal lengths
from itertools import zip_longest
for a, b in zip_longest(list_a, list_b, fillvalue=None):
    ...

# ❌ Avoid
for i in range(len(items)):
    print(f"{i}: {items[i]}")
```

## Walrus Operator (:=)

```python
# ✅ Avoid repeated computation
if (count := len(items)) > 10:
    print(f"Too many: {count}")

# ✅ In comprehension
results = [
    processed
    for item in items
    if (processed := transform(item)) is not None
]

# ✅ While loop
while (line := file.readline()):
    process(line)
```

## Avoid for-else

```python
# ✅ Return early
def find_target(items: list[int], target: int) -> int | None:
    for i, item in enumerate(items):
        if item == target:
            return i
    return None

# ❌ Confusing else block
for i, item in enumerate(items):
    if item == target:
        break
else:
    i = None  # Not obvious when this runs
```
