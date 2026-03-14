"""Domain managers for DocForge.

High-level managers that orchestrate complex domain logic:
- ConfigManager: config loading and validation
- RulebookManager: load, validate, and diff rulebooks
- ContextManager: extract product context from repo/docs
"""

from docforge.core.managers.config import CompositeConfigAdapter
from docforge.core.managers.context import ContextManager
from docforge.core.managers.rulebook import RulebookManager

__all__ = [
    "CompositeConfigAdapter",
    "RulebookManager",
    "ContextManager",
]
