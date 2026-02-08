import asyncio
from validator import validate_dict_str_int


def run_test(name:str, test_function):
    """
    helper to run test and print result
    """
    try:
        test_function()
        print(f" {name}")
    except AssertionError as e:
        print(f"{name} : {e}")
    except Exception as e:
        print(f"✗ {name}: Unexpected error - {e}")
    

# ============== TEST FUNCTIONS ==============

@validate_dict_str_int
def sum_values(data: dict[str, int]) -> int:
    """
    summing values
    """
    return sum(data.values())


@validate_dict_str_int
def multi_param(data: dict[str, int], multiplier: int, name: str) -> int:
    """Function with multiple params - only data should be validated."""
    return sum(data.values()) * multiplier


@validate_dict_str_int
def optional_param(data: dict[str, int] = None) -> int:
    """Function with optional dict parameter."""
    if data is None:
        return 0
    return sum(data.values())


@validate_dict_str_int
def returns_dict(data: dict[str, int]) -> dict[str, int]:
    """Function that returns dict[str, int] - tests 'return' hint skipping."""
    data["processed"] = 1
    return data


@validate_dict_str_int
async def async_sum(data: dict[str, int]) -> int:
    """Async function to test async support."""
    return sum(data.values())

# ============== TESTS ==============

def test_valid_input():
    result = sum_values({"a": 1, "b": 2, "c": 3})
    assert result == 6, f"Expected 6, got {result}"


def test_empty_dict():
    result = sum_values({})
    assert result == 0, f"Expected 0, got {result}"


def test_large_integers():
    result = sum_values({"big": 10**18, "negative": -500})
    assert result == 10**18 - 500


def test_bool_value_rejected():
    try:
        sum_values({"flag": True})
        assert False, "Should have raised TypeError"
    except TypeError as e:
        assert "bool" in str(e).lower()


def test_non_string_key_rejected():
    try:
        sum_values({123: 456})
        assert False, "Should have raised TypeError"
    except TypeError as e:
        assert "str" in str(e).lower()


def test_float_value_rejected():
    try:
        sum_values({"price": 19.99})
        assert False, "Should have raised TypeError"
    except TypeError as e:
        assert "float" in str(e)


def test_string_value_rejected():
    try:
        sum_values({"name": "alice"})
        assert False, "Should have raised TypeError"
    except TypeError as e:
        assert "str" in str(e)


def test_not_a_dict():
    try:
        sum_values("not a dict")
        assert False, "Should have raised TypeError"
    except TypeError as e:
        assert "dict" in str(e).lower()


def test_none_rejected_when_required():
    try:
        sum_values(None)
        assert False, "Should have raised TypeError"
    except TypeError as e:
        assert "NoneType" in str(e)


def test_multi_param_validates_only_dict():
    # Valid dict, other params are not validated
    result = multi_param({"x": 5}, 3, "test")
    assert result == 15

    # Invalid dict should fail
    try:
        multi_param({"x": "bad"}, 3, "test")
        assert False, "Should have raised TypeError"
    except TypeError:
        pass


def test_optional_param_with_none():
    result = optional_param()  # Uses default None
    assert result == 0


def test_optional_param_with_value():
    result = optional_param({"a": 10})
    assert result == 10


def test_return_type_hint_ignored():
    # Should not crash even though return type is dict[str, int]
    result = returns_dict({"a": 1})
    assert result == {"a": 1, "processed": 1}


def test_async_function():
    result = asyncio.run(async_sum({"a": 5, "b": 10}))
    assert result == 15


def test_async_function_validation():
    try:
        asyncio.run(async_sum({"bad": True}))
        assert False, "Should have raised TypeError"
    except TypeError as e:
        assert "bool" in str(e).lower()


def test_preserves_function_metadata():
    
    assert sum_values.__name__ == "sum_values"
    assert "sum" in sum_values.__doc__.lower() or "Sum" in sum_values.__doc__


# ============== RUN ALL TESTS ==============

if __name__ == "__main__":
    print("Running tests...\n")

    tests = [
        ("Valid input", test_valid_input),
        ("Empty dict", test_empty_dict),
        ("Large integers", test_large_integers),
        ("Bool value rejected", test_bool_value_rejected),
        ("Non-string key rejected", test_non_string_key_rejected),
        ("Float value rejected", test_float_value_rejected),
        ("String value rejected", test_string_value_rejected),
        ("Not a dict", test_not_a_dict),
        ("None rejected when required", test_none_rejected_when_required),
        ("Multi-param validates only dict", test_multi_param_validates_only_dict),
        ("Optional param with None", test_optional_param_with_none),
        ("Optional param with value", test_optional_param_with_value),
        ("Return type hint ignored", test_return_type_hint_ignored),
        ("Async function works", test_async_function),
        ("Async function validates", test_async_function_validation),
        ("Preserves function metadata", test_preserves_function_metadata),
    ]

    for name, test_func in tests:
        run_test(name, test_func)

    print("\nDone!")