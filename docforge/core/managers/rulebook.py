"""Rulebook management and validation."""

import difflib
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from docforge.core.interfaces.adapters import StorageAdapter


class RulebookMetadata:
    """Metadata about a rulebook."""

    def __init__(
        self,
        name: str,
        category: str,
        version: str,
        path: Path,
        content: str,
    ):
        self.name = name
        self.category = category
        self.version = version
        self.path = path
        self.content = content
        self.created_at: Optional[str] = None
        self.modified_at: Optional[str] = None


class RulebookManager:
    """Manages rulebook loading, validation, and comparison.
    
    Responsibilities:
    - Load rulebooks from filesystem
    - Validate rulebook structure and content
    - Detect changes between rulebook versions
    - Store rulebooks in versioned artifacts
    """

    def __init__(self, rulebooks_dir: Union[str, Path], storage: Optional[StorageAdapter] = None):
        """Initialize rulebook manager.
        
        Args:
            rulebooks_dir: Directory containing rulebooks
            storage: Optional storage adapter for versioning
        """
        self.rulebooks_dir = Path(rulebooks_dir)
        self.storage = storage
        self._cache: Dict[str, RulebookMetadata] = {}

    def load(self, name: str) -> Optional[RulebookMetadata]:
        """Load a rulebook by name.
        
        Args:
            name: Rulebook name (e.g., "engineering", "writing")
            
        Returns:
            RulebookMetadata or None if not found
        """
        if name in self._cache:
            return self._cache[name]

        # Search for rulebook file
        for rulebook_file in self.rulebooks_dir.rglob(f"{name}*rulebook.md"):
            try:
                content = rulebook_file.read_text(encoding="utf-8")
                category = rulebook_file.parent.name

                metadata = RulebookMetadata(
                    name=name,
                    category=category,
                    version="1.0",
                    path=rulebook_file,
                    content=content,
                )

                self._cache[name] = metadata
                return metadata
            except Exception:
                continue

        return None

    def list_all(self) -> List[RulebookMetadata]:
        """List all available rulebooks.
        
        Returns:
            List of RulebookMetadata
        """
        rulebooks: List[RulebookMetadata] = []

        for rulebook_file in self.rulebooks_dir.rglob("*rulebook.md"):
            try:
                content = rulebook_file.read_text(encoding="utf-8")
                name = rulebook_file.stem.replace("-rulebook", "")
                category = rulebook_file.parent.name

                metadata = RulebookMetadata(
                    name=name,
                    category=category,
                    version="1.0",
                    path=rulebook_file,
                    content=content,
                )
                rulebooks.append(metadata)
            except Exception:
                continue

        return rulebooks

    def validate(self, rulebook: RulebookMetadata) -> List[str]:
        """Validate rulebook structure and content.
        
        Args:
            rulebook: Rulebook to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors: List[str] = []

        # Check basic structure
        if not rulebook.content.strip():
            errors.append("Rulebook is empty")

        # Check for required sections
        if "## Purpose" not in rulebook.content:
            errors.append("Missing '## Purpose' section")

        # Check markdown formatting
        lines = rulebook.content.split("\n")
        if lines and not lines[0].startswith("#"):
            errors.append("Missing title (# heading)")

        return errors

    def store(self, rulebook: RulebookMetadata) -> bool:
        """Store rulebook in versioned artifacts.
        
        Args:
            rulebook: Rulebook to store
            
        Returns:
            True if stored successfully
        """
        if not self.storage:
            return False

        try:
            import asyncio
            asyncio.run(self.storage.save(
                path=f"rulebooks/{rulebook.category}/{rulebook.name}.md",
                content=rulebook.content,
                artifact_type="rulebook",
                metadata={
                    "name": rulebook.name,
                    "category": rulebook.category,
                    "version": rulebook.version,
                },
            ))
            return True
        except Exception:
            return False

    def diff(self, rulebook1: RulebookMetadata, rulebook2: RulebookMetadata) -> str:
        """Generate diff between two versions.
        
        Args:
            rulebook1: First rulebook
            rulebook2: Second rulebook
            
        Returns:
            Human-readable diff string
        """
        lines1 = rulebook1.content.splitlines(keepends=True)
        lines2 = rulebook2.content.splitlines(keepends=True)

        diff = difflib.unified_diff(
            lines1,
            lines2,
            fromfile=f"{rulebook1.name} v{rulebook1.version}",
            tofile=f"{rulebook2.name} v{rulebook2.version}",
        )

        return "".join(diff)
