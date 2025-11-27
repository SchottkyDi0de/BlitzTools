import traceback
from typing import Callable, Tuple, Any

class Logger:
    def warning(self, msg: str) -> None:
        pass

    def error(self, msg: str) -> None:
        pass

def wrap_exceptions(logger: Logger, ignore_exceptions: Tuple[type, ...]) -> Callable[..., Callable[..., Any]]:
    """
    A decorator that wraps a function to catch and handle exceptions.

    Args:
        logger (Logger): The logger to use for logging warnings and errors.
        ignore_exceptions (Tuple[type, ...]): A tuple of exception types to ignore.

    Returns:
        Callable[..., Callable..., Any]]: A decorator that takes a function as an argument and returns a new function that wraps the original function.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., None]:
        def wrapper(*args: Any, **kwargs: Any) -> None:
            try:
                func(*args, **kwargs)
            except Exception as e:
                if e in ignore_exceptions:
                    logger.warning(traceback.format_exc())
                    return
                
                logger.error(traceback.format_exc())
                raise e

        return wrapper

    return decorator
