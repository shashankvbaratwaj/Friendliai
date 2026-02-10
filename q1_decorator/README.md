# Q1: dict[str, int] Validator Decorator

A Python 3.11+ decorator that validates function arguments annotated as `dict[str, int]` at runtime.

---

## Problem Statement

> Implement a Python 3.11+ decorator that ensures only variables of type `dict[str, int]` are passed to the original function.

**Context**: In a large monorepo, many functions across API services, data pipelines, CLI tools, and billing jobs share a common signature — accepting dictionaries with string keys and integer values. This decorator provides a shared validation utility to reduce duplicated logic and improve developer experience.

---

## Quick Start

```bash
# Run all tests
python3 test_validator.py

# Expected output: 16 passing tests
```

---

## Solution Architecture

### Core Components

The solution is structured into focused, single-responsibility functions:

```
validate_dict_str_int(func)     # Main decorator - entry point
    │
    ├── is_dict_str_int(hint)        # Checks if type hint matches dict[str, int]
    │
    ├── _validate_arguments(...)      # Extracts and validates annotated parameters
    │
    └── validate_value(value, name)   # Validates actual dict structure
```

### Why This Structure?

1. **`is_dict_str_int(hint)`** — Separated because type hint checking uses `get_origin()` and `get_args()` which is a distinct responsibility from value validation.

2. **`_validate_arguments(func, args, kwargs)`** — Extracted to handle the complexity of binding arguments to parameter names and iterating through type hints. This also enabled clean async support (both wrappers share this function).

3. **`validate_value(value, param_name)`** — Isolated validation logic makes it easy to test and provides clear, specific error messages.

---

## Key Design Decisions

### 1. Validate Only Type-Hinted Parameters

We validate parameters annotated as `dict[str, int]`, not all arguments.

**Reasoning**: Functions in production contexts often have additional parameters (flags, multipliers, configs). This approach makes the decorator a flexible, reusable utility.

```python
@validate_dict_str_int
def process(data: dict[str, int], multiplier: int, verbose: bool):
    # Only 'data' is validated — multiplier and verbose are untouched
```

### 2. Reject Boolean Values

`{"flag": True}` raises TypeError, even though `bool` is a subclass of `int`.

**Reasoning**: In billing and counting contexts, accepting `True` as `1` is a subtle bug waiting to happen. Explicit rejection prevents errors.

### 3. Handling of Optional Parameters

```python
@validate_dict_str_int
def process(data: dict[str, int] = None):  # None is allowed here
    if data is None:
        return 0
    return sum(data.values())
```

**Reasoning**: If a developer sets `= None` as default, they intend to handle that case. We validate structure when a dict is provided, but respect intentional design choices.

### 4. Async Function Support

The decorator detects async functions and returns the appropriate wrapper:

```python
if asyncio.iscoroutinefunction(func):
    return async_wrapper   # Uses: return await func(...)
return sync_wrapper        # Uses: return func(...)
```

**Reasoning**: Async functions return coroutine objects that must be awaited. Without proper handling, the decorator would break async function behavior.



---

## Edge Cases Handled

| Case | Behavior | Reasoning |
|------|----------|-----------|
| Empty dict `{}` | Valid | Satisfies `dict[str, int]` contract |
| Bool values | Rejected | Prevents subtle bugs in counting contexts |
| Non-string keys | Rejected | Keys must be strings |
| Non-int values | Rejected | Values must be integers |
| None (required param) | Rejected | No default means dict is required |
| None (optional param) | Allowed | Respects developer's intentional design |
| Return type `-> dict[str, int]` | Ignored | Return hints are not parameters |
| Async functions | Supported | Properly awaits coroutines |
| Dict subclasses | Accepted | OrderedDict, defaultdict work (Liskov substitution) |

---

## Test Coverage

```bash
$ python3 test_validator.py

Running tests...

✓ Valid input
✓ Empty dict
✓ Large integers
✓ Bool value rejected
✓ Non-string key rejected
✓ Float value rejected
✓ String value rejected
✓ Not a dict
✓ None rejected when required
✓ Multi-param validates only dict
✓ Optional param with None
✓ Optional param with value
✓ Return type hint ignored
✓ Async function works
✓ Async function validates
✓ Preserves function metadata

Done!
```

---

## Usage Examples

### Basic Usage
```python
from validator import validate_dict_str_int

@validate_dict_str_int
def process_billing(data: dict[str, int]) -> int:
    return sum(data.values())

process_billing({"item_a": 10, "item_b": 20})  # Returns 30
```

### Multiple Parameters
```python
@validate_dict_str_int
def calculate(data: dict[str, int], multiplier: int) -> int:
    return sum(data.values()) * multiplier

calculate({"a": 5}, 3)  # Returns 15
```

### Optional Parameter
```python
@validate_dict_str_int
def process(data: dict[str, int] = None) -> int:
    if data is None:
        return 0
    return sum(data.values())

process()           # Returns 0
process({"a": 10})  # Returns 10
```

### Async Function
```python
@validate_dict_str_int
async def fetch_totals(params: dict[str, int]) -> int:
    return sum(params.values())

await fetch_totals({"limit": 100})  # Returns 100
```

---

## Files

```
q1_decorator/
├── validator.py       # Main decorator implementation
├── test_validator.py  # Comprehensive test suite (16 tests)
└── README.md          # This file
```

---

## Requirements

- Python 3.11+
- No external dependencies (standard library only)

---

## Author

Shashank V Baratwaj 
