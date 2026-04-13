# Error Handling

> try/except/else/finally, custom exceptions.

## try/except/else/finally

```python
def process_file(path: Path) -> Result:
    try:
        data = path.read_text()
    except FileNotFoundError:
        logger.warning(f"Not found: {path}")
        return Result.empty()
    except PermissionError as e:
        raise ProcessingError(f"Cannot read {path}") from e
    else:
        # Runs if no exception
        logger.info(f"Read {path}")
        return Result(data=data)
    finally:
        # Always runs
        cleanup()
```

## Custom Exceptions

```python
class DocConverterError(Exception):
    """Base exception for DocConverter."""

class UnsupportedConversionError(DocConverterError):
    """Raised when conversion format is not supported."""

    def __init__(self, source: str, target: str):
        self.source = source
        self.target = target
        super().__init__(f"Unsupported conversion: {source} → {target}")
```
