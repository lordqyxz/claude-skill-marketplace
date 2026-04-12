# Lists and Dictionaries

> Comprehensions, dictionary patterns, sorting.

## Comprehensions

```python
# ✅ List comprehension
squares = [x**2 for x in range(10) if x % 2 == 0]

# ✅ Set comprehension
unique = {x.lower() for x in items}

# ✅ Dict comprehension
scores = {name: score for name, score in zip(names, scores)}

# ✅ Generator expression (memory efficient)
sum(x**2 for x in range(1_000_000))

# ❌ Limit to 2 expressions
# Too complex:
result = [y for x in data if x > 0 for y in transform(x) if y.valid]

# Better: split into steps
valid_data = [x for x in data if x > 0]
results = [y for x in valid_data for y in transform(x) if y.valid]
```

## Dictionary Patterns

```python
from collections import defaultdict, Counter

# ✅ get with default
count = word_counts.get(word, 0)

# ✅ Counter for counting
word_counts = Counter(text.split())
top_10 = word_counts.most_common(10)

# ✅ defaultdict for grouping
groups = defaultdict(list)
for key, value in pairs:
    groups[key].append(value)

# ✅ setdefault
data.setdefault(key, []).append(value)
```

## Sorting

```python
# ✅ Key function
sorted_items = sorted(items, key=lambda x: x.name)
sorted_items = sorted(items, key=lambda x: (x.priority, -x.timestamp))

# ✅ Reverse sort
sorted_desc = sorted(items, reverse=True)

# ✅ In-place sort
items.sort(key=lambda x: x.name)
```
