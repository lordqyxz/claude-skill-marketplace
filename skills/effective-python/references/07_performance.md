# Performance

> Timing, caching, memory optimization patterns.

## Timing

```python
import time

# ✅ High-precision timing
start = time.perf_counter()
# ... operation ...
elapsed = time.perf_counter() - start
print(f"Elapsed: {elapsed:.6f}s")

# ✅ Nanosecond precision
start_ns = time.perf_counter_ns()
```

## Caching

```python
import functools

# ✅ lru_cache
@functools.lru_cache(maxsize=128)
def expensive_computation(n: int) -> int:
    return n ** 2

# ✅ Clear cache
expensive_computation.cache_clear()

# ℹ️ Cache info
info = expensive_computation.cache_info()
# CacheInfo(hits=10, misses=5, maxsize=128, currsize=5)
```

## Memory

```python
# ✅ __slots__ reduces memory
class Point:
    __slots__ = ("x", "y")
    # ~40% less memory than regular class

# ✅ Generator for large data
def read_large_file(path: Path) -> Iterator[str]:
    with open(path) as f:
        for line in f:
            yield line.strip()

# ❌ Don't load all into memory
# lines = list(read_large_file(path))  # Bad for large files
```
