# Python Testing Patterns

Reference for writing tests with pytest — loaded when writing test code, using fixtures, or mocking.

## Testing Philosophy

Tests give you confidence to change code. Good tests are:
- **Deterministic**: Same input, same output, every time. No random, no `time.now()`, no network.
- **Fast**: A test suite that takes minutes doesn't get run. Target seconds.
- **Independent**: Each test sets up and tears down its own world. No implicit ordering.

## pytest Essentials

### Structure: Arrange → Act → Assert

```python
def test_user_creation():
    # Arrange
    db = InMemoryDatabase()
    user = User(name="Alice", age=30)

    # Act
    db.add(user)

    # Assert
    assert db.get("Alice") == user
```

### Fixture scope — don't over-share

```python
@pytest.fixture
def db():  # Default scope: function — new per test
    return InMemoryDatabase()

@pytest.fixture(scope="session")
def schema():  # Once per test session
    return load_schema("users.json")
```

Why: Over-scoped fixtures create hidden dependencies between tests. Test A modifies the fixture, test B sees the modification. Default to function scope; widen only when setup is expensive AND the fixture is read-only.

### Fixture composition

```python
@pytest.fixture
def user(db):
    u = User(name="Alice")
    db.add(u)
    return u

def test_user_retrieval(db, user):
    assert db.get(user.name) == user
```

Fixtures that depend on other fixtures are the pytest way to build test data. This is clearer than setup/teardown inheritance.

### `tmp_path` — built-in fixture for temp files

```python
def test_file_export(tmp_path):
    output = tmp_path / "result.csv"
    export_data([1, 2, 3], output)
    assert output.read_text() == "1\n2\n3\n"
```

Prefer `tmp_path` (pathlib) over `tmpdir` (py.path). No need to manually clean up.

## Parametrize — One Test, Many Cases

```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("", ""),
    ("123", "123"),
])
def test_upper(input, expected):
    assert input.upper() == expected
```

Why: Each parametrized case shows up as a separate test in the report. One failure doesn't hide the others, and the test name includes the parameters.

For complex cases, use `pytest.param` with IDs:

```python
@pytest.mark.parametrize("user,can_access", [
    pytest.param(User(role="admin"), True, id="admin"),
    pytest.param(User(role="guest"), False, id="guest"),
    pytest.param(User(role=""), False, id="empty-role"),
])
def test_access_control(user, can_access):
    assert check_access(user) is can_access
```

## Mocking — Use Sparingly

Mock when the real dependency is slow, non-deterministic, or has side effects (HTTP calls, database, filesystem). Don't mock what you own.

### `unittest.mock` via pytest

```python
from unittest.mock import patch, MagicMock

def test_fetch_user():
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = {"name": "Alice"}
        result = fetch_user(1)
        assert result.name == "Alice"
        mock_get.assert_called_once_with("https://api.example.com/users/1")
```

### `spy` pattern — verify calls without replacing

```python
from unittest.mock import patch

def test_cache_hit():
    with patch("module.expensive_lookup", wraps=module.expensive_lookup) as spy:
        result1 = cached_lookup("key")
        result2 = cached_lookup("key")
        assert spy.call_count == 1  # Only called once, second was cache hit
```

`wraps=` calls the real function but records calls. Use when you want to verify interaction patterns without breaking behavior.

### Fixture-based mocking

```python
@pytest.fixture
def mock_http():
    with patch("httpx.get") as mock:
        mock.return_value.status_code = 200
        mock.return_value.json.return_value = {"data": []}
        yield mock

def test_api_call(mock_http):
    result = fetch_data()
    assert result == {"data": []}
```

## Async Testing

```python
@pytest.mark.asyncio
async def test_async_fetch():
    result = await fetch_data("url")
    assert result is not None

# With pytest-asyncio, configure in pyproject.toml:
# [tool.pytest.ini_options]
# asyncio_mode = "auto"
```

## Test Organization

```
tests/
├── conftest.py          # Shared fixtures
├── unit/                # Fast, no I/O
│   ├── test_models.py
│   └── test_utils.py
├── integration/         # Real dependencies (DB, API)
│   ├── test_repository.py
│   └── test_api.py
└── conftest.py          # Root-level fixtures
```

Mark integration tests:

```python
@pytest.mark.integration
def test_database_query():
    ...
```

Run only unit tests: `pytest -m "not integration"`

## Anti-Patterns

1. **Testing implementation details**: Tests that check private methods or mock internal collaborators. If you refactor, these break even though behavior is correct. Test the public interface.
2. **Assertion roulette**: A test with 20 `assert` statements where you don't know which one failed. Use separate test functions or `pytest-assume` for multiple independent assertions.
3. **Hard-coded dates/times**: `datetime(2024, 1, 1)` everywhere. Use `freezegun` or inject a clock.
4. **Over-mocking**: Every dependency is a mock. The test proves the mocks return what you told them to return — not that the real system works. Prefer real dependencies in integration tests.