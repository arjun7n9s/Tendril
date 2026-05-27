"""Helpers for ORM model values.

SQLAlchemy stores enum-typed String columns as plain strings on read, so
direct attribute access returns either an Enum or a str depending on the
state. `as_str` normalizes both.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


def as_str(value: Any) -> str:
    if isinstance(value, Enum):
        return value.value
    return str(value) if value is not None else ""
