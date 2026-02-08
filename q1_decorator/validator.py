import functools
import inspect
from typing import Callable, Any, get_type_hints, get_origin, get_args
import asyncio



def is_dict_str_int(hint) -> bool:
    """
    Check if type hint is dict[str,int]
    """
    return get_origin(hint) is dict and get_args(hint) == (str,int)

def validate_value(value: Any, param_name:str) -> None:
    """
    Validate the value is in dict[str,int] format
    Raise Type error if otherwise
    """
    #check if dict
    if not isinstance(value, dict):
        raise TypeError(
            f"Parameter '{param_name}' expected dict[str,int] "
            f"got {type(value).__name__}"
        )

    #check if key:string val:int 
    for key,val in value.items():
        if not isinstance(key,str):
            raise TypeError(
                f"Parameter '{param_name}' expected dict[str,int], "
                f"but key {key!r} is {type(key).__name__}, not str"
            )
        #check if the int value is not Boolean
        if isinstance(val,bool):
            raise TypeError(
                f"Parameter '{param_name}' expected dict[str, int], "
                f"but key '{key}' has value {val!r} of type bool "
                f"(bool is not allowed, use int)"
            )
        #check if val is int 
        if not isinstance(val, int):
            raise TypeError(
                    f"Parameter '{param_name}' expected dict[str, int], "
                    f"but key '{key}' has value {val!r} of type {type(val).__name__}"
                )

def _validate_arguments(func: Callable, args: tuple, kwargs: dict) -> None:
    """
    Helper to validate dict[str,int] arguments.
    """
    sig = inspect.signature(func)
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()

    hints = get_type_hints(func)

    for param_name, hint in hints.items():
        if param_name == "return":
            continue
        if is_dict_str_int(hint):
            value = bound.arguments.get(param_name)

            #allow none only if parameter has none as default
            if value is None:
                param = sig.parameters.get(param_name)
                if param is not None and param.default is None:
                    continue
                
            validate_value(value, param_name)

def validate_dict_str_int(func: Callable) -> Callable:
    """
    Decorator that validates arguments annotated as dict[str,int] , supports async and sync functions 
    """

    @functools.wraps(func) # using this to preserve metadata of a function
    def sync_wrapper(*args, **kwargs) -> Any:
        _validate_arguments(func,args,kwargs)
        return func(*args, **kwargs)

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        _validate_arguments(func, args, kwargs)
        return await func(*args, **kwargs)

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper 