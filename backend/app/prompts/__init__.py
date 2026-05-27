"""Prompt template loaders.

Templates live as `.md` files in this directory; the module exposes
helpers to load and format them.
"""

from __future__ import annotations

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent


def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"prompt template not found: {path}")
    return path.read_text(encoding="utf-8")


def render_prompt(name: str, **fields: object) -> str:
    return load_prompt(name).format(**fields)
