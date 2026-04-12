# Async Patterns and Concurrency

Reference for async Python — loaded when building async services, using TaskGroup, or mixing sync/async.

## When to Use Which Concurrency Model

| Model | Best For | Avoid When |
|-------|----------|------------|
| `asyncio` | I/O-bound (HTTP, DB, files) | CPU-heavy computation |
| `concurrent.futures.ThreadPoolExecutor` | I/O-bound legacy code, blocking APIs | You need shared mutable state |
| `concurrent.futures.ProcessPoolExecutor` | CPU-bound (math, image processing) | Tasks need shared memory |
| `threading` | Rarely — prefer executors | Almost everything |

## asyncio Core Patterns

### TaskGroup (3.11+) — The modern way

```python
async def fetch_all(urls: list[str]) -> list[Response]:
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(fetch(url)) for url in urls]
    return [t.result() for t in tasks]
```

Why TaskGroup beats `gather`: If any task raises, TaskGroup cancels the others automatically. With `gather`, orphaned tasks keep running. TaskGroup also provides a clean `async with` boundary.

### Timeout (3.11+)

```python
async with asyncio.timeout(5.0):
    await slow_operation()
```

Prefer `asyncio.timeout()` over `asyncio.wait_for()` — it integrates better with TaskGroup and cancellation scopes.

### Cancellation handling

```python
async def long_task():
    try:
        await asyncio.sleep(3600)
    except asyncio.CancelledError:
        await cleanup()  # Must await before re-raising
        raise  # Always re-raise unless you truly want to suppress
```

Why: Swallowing `CancelledError` silently prevents proper shutdown. Always re-raise unless you have an explicit reason not to.

## Mixing Sync and Async

The golden rule: don't. If a call stack is async, everything down it should be async. When you must bridge:

### Running sync code from async — `run_in_executor`

```python
async def main():
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, blocking_function, arg1, arg2)
```

### Running async code from sync — `asyncio.run`

```python
def sync_entry_point():
    result = asyncio.run(async_function())
```

**Never** call `asyncio.run()` from within an already-running event loop. Use `loop.run_until_complete()` if you're inside a loop (but this is usually a design smell).

### The "sync wrapper" anti-pattern

Avoid this:

```python
def fetch_data():  # Looks sync, secretly runs async
    return asyncio.run(_async_fetch())
```

This creates a new event loop per call — expensive and breaks if called from async code. Instead, make the async version the canonical API.

## Common Async Pitfalls

1. **Forgetting `await`**: `result = fetch()` instead of `result = await fetch()` — you get a coroutine object, not the result. Type checkers with strict settings catch this.
2. **Blocking the event loop**: `time.sleep()`, `requests.get()`, or any CPU-bound work in async code blocks ALL other tasks. Always offload to executor.
3. **Creating tasks without holding references**: `asyncio.create_task(coro)` — if you don't store the task, it can be garbage collected mid-execution.

```python
# BAD — task may be GC'd
asyncio.create_task(background_work())

# GOOD — keep the reference
task = asyncio.create_task(background_work())
background_tasks.add(task)
task.add_done_callback(background_tasks.discard)
```

4. **Semaphore for rate limiting**:
```python
sem = asyncio.Semaphore(10)

async def fetch_limited(url: str) -> Response:
    async with sem:
        return await fetch(url)
```

5. **Async generators need `async for`**:
```python
async def stream_rows():
    async for row in cursor:
        yield row

# Consume with:
async for row in stream_rows():
    process(row)
```

## Structured Concurrency Pattern

Organize async code so task lifetimes are bounded by scope — no "fire and forget":

```python
async def app():
    async with asyncio.TaskGroup() as tg:
        tg.create_task(monitor_health())
        tg.create_task(handle_requests())
        # Both tasks are cancelled if either fails
        # Both are awaited when exiting the block
```

This is the async equivalent of RAII — resources don't leak, tasks don't orphan.