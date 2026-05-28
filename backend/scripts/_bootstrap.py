"""Sys.path bootstrap for scripts invoked as a file path.

Importing this module first ensures `import app.*` works whether the
script is run via `uv run python -m scripts.foo` or
`uv run python scripts/foo.py`. Either invocation should produce the
same result.
"""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_root_str = str(_BACKEND_ROOT)
if _root_str not in sys.path:
    sys.path.insert(0, _root_str)
