import sys

import loguru

_logger = loguru.logger
_logger.remove()

# stdout: DEBUG & INFO
_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

def level_filter(level_name):
    return lambda record: record["level"].name == level_name

_formats = {
    "INFO":  "<blue>{time:YYYY-MM-DD HH:mm:ss}</blue>  | <level>{level: <8}</level> | {message}",
    "DEBUG": "<blue>{time:YYYY-MM-DD HH:mm:ss}</blue> | <level>{level: <8}</level> | <underline>{file}:{line}</underline> in {function}\n>>> <cyan>{message}</cyan>",
    "WARNING":"<blue>{time:YYYY-MM-DD HH:mm:ss}</blue> | <level>{level: <8}</level> | <underline>{file}:{line}</underline> in {function}\n>>> <yellow>{message}</yellow>",
    "ERROR": "<blue>{time:YYYY-MM-DD HH:mm:ss}</blue> | <level>{level: <8}</level> | <underline>{file}:{line}</underline> in {function}\n>>>  <magenta>{message}</magenta>",
    "CRITICAL":"<blue>{time:YYYY-MM-DD HH:mm:ss}</blue> | <level>{level: <8}</level> | <underline>{file}:{line}</underline> in {function}\n>>> <red><reverse>{message}</reverse></red>"
}

for lvl in _levels:
    stream = sys.stdout if lvl in ("DEBUG","INFO") else sys.stderr
    _logger.add(
        stream,
        level=lvl,
        filter=level_filter(lvl),
        format=_formats[lvl],
        colorize=True,
        enqueue=True,
    )

def get_logger(name: str) -> loguru.Logger:
    """
    Returns a logger bound to the given name.

    Args:
        name (str): The name to bind to the logger.

    Returns:
        loguru.Logger: The bound logger.
    """
    return _logger.bind(name=name)

# TODO: Реализовать запись логов в файл через добавления Callable в sink logger.py:24
# TODO: Реализовать атоочиску логов при достижении определенного размера