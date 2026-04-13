# Concurrency

> ThreadPoolExecutor, ProcessPoolExecutor, asyncio, thread safety.

## ThreadPoolExecutor

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

# ✅ For IO-bound work
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = {executor.submit(fetch, url): url for url in urls}
    results = {}
    for future in as_completed(futures):
        url = futures[future]
        try:
            results[url] = future.result()
        except Exception as e:
            logger.error(f"Failed {url}: {e}")
```

## ProcessPoolExecutor

```python
from concurrent.futures import ProcessPoolExecutor

# ✅ For CPU-bound work
with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_file, files))
```

## asyncio

```python
import asyncio

# ✅ Concurrent coroutines
async def fetch_all(urls: list[str]) -> list[Response]:
    tasks = [fetch(url) for url in urls]
    return await asyncio.gather(*tasks)

# ✅ With timeout
async def fetch_with_timeout(url: str, timeout: float = 10.0) -> Response | None:
    try:
        async with asyncio.timeout(timeout):
            return await fetch(url)
    except asyncio.TimeoutError:
        return None

# ✅ Run
results = asyncio.run(fetch_all(urls))
```

## Thread Safety

```python
import threading
import queue

# ✅ Lock for shared state
class Counter:
    def __init__(self):
        self._value = 0
        self._lock = threading.Lock()

    def increment(self) -> int:
        with self._lock:
            self._value += 1
            return self._value

# ✅ Queue for producer-consumer
def producer(q: queue.Queue, items: list[int]) -> None:
    for item in items:
        q.put(item)
    q.put(None)  # Sentinel

def consumer(q: queue.Queue, results: list[int]) -> None:
    while (item := q.get()) is not None:
        results.append(item * 2)
        q.task_done()
```
