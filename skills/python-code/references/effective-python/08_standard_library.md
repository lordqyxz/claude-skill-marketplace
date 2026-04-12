# Standard Library

> pathlib, logging, collections.

## pathlib

```python
from pathlib import Path

# ✅ Path operations
data_dir = Path("data")
config = data_dir / "config.json"
home = Path.home()

# ✅ Check existence
if config.exists():
    content = config.read_text()

# ✅ Glob patterns
for file in data_dir.glob("**/*.json"):
    process(file)

# ✅ Create directories
output_dir.mkdir(parents=True, exist_ok=True)
```

## logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

def process(data: bytes) -> Result:
    logger.debug(f"Processing {len(data)} bytes")
    try:
        result = transform(data)
        logger.info("Processing completed")
        return result
    except Exception:
        logger.exception("Processing failed")
        raise
```

## collections

```python
from collections import defaultdict, Counter, deque, ChainMap

# Counter - counting
counts = Counter(items)
top = counts.most_common(10)

# defaultdict - grouping
groups = defaultdict(list)

# deque - queue with fast append/pop from both ends
queue = deque(maxlen=100)  # Bounded

# ChainMap - combined dictionaries
defaults = {"timeout": 30, "retry": 3}
config = ChainMap(user_settings, defaults)
```
