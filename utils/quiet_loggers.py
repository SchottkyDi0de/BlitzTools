from __future__ import annotations

import logging

_QUIET_LOGGER_NAMES = (
    "PIL",
    "urllib3",
    "urllib3.connectionpool",
    "charset_normalizer",
)


def quiet_third_party_loggers() -> None:
    for name in _QUIET_LOGGER_NAMES:
        logging.getLogger(name).setLevel(logging.WARNING)
