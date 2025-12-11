
import traceback
import logging
from typing import Callable, Tuple, Any

def wrap_exceptions(
        logger: logging.Logger, 
        ignore_exceptions: Tuple[type, ...],
        short_name: str = "Error Handler"
    ) -> Callable[..., Callable[..., Any]]:
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
                    logger.warning(f"{short_name}: {e.__class__.__name__} {e} in {func.__name__}()")
                    logger.warning(traceback.format_exc())
                    return
                
                logger.error(f"{short_name}: {e.__class__.__name__} {e} in {func.__name__}()")
                logger.error(traceback.format_exc())
                raise e

        return wrapper

    return decorator
