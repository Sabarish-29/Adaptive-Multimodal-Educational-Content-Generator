"""Project logging helpers.

Intentionally separate from stdlib ``logging`` to avoid shadowing.
Add any project-specific logging utility functions here.
"""
from __future__ import annotations
import logging

def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(name or "adaptive")

__all__ = ["get_logger"]
