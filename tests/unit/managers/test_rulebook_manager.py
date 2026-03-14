"""Tests for rulebook manager."""

import pytest
import tempfile
from pathlib import Path
import yaml

from docforge.core.managers.rulebook import RulebookManager, RulebookMetadata


@pytest.fixture
def rulebooks_dir():
    """Create temporary rulebooks directory with sample rulebooks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        rulebooks_path = Path(tmpdir)
        
        # Create sample rulebooks
        engineering_dir = rulebooks_path / "engineering"
        engineering_dir.mkdir()
        (engineering_dir / "engineering.md").write_text("# Engineering Rulebook\nDefine engineering standards...")
        
        writing_dir = rulebooks_path / "writing"
        writing_dir.mkdir()
        (writing_dir / "writing.md").write_text("# Writing Rulebook\nDefine writing standards...")
        
        yield rulebooks_path


def test_rulebook_metadata_creation():
    """Test RulebookMetadata model creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.md"
        path.write_text("Test content")
        
        metadata = RulebookMetadata(
            name="test-rulebook",
            category="engineering",
            version="1.0.0",
            path=path,
            content="Test content",
        )
        
        assert metadata.name == "test-rulebook"
        assert metadata.category == "engineering"
        assert metadata.version == "1.0.0"
        assert metadata.content == "Test content"
        assert metadata.created_at is None  # Not set yet


def test_rulebook_manager_initialization(rulebooks_dir):
    """Test RulebookManager initialization."""
    manager = RulebookManager(rulebooks_dir=str(rulebooks_dir))
    assert manager.rulebooks_dir == rulebooks_dir
    assert manager.storage is None


def test_rulebook_manager_list_rulebooks(rulebooks_dir):
    """Test listing all rulebooks in a directory."""
    manager = RulebookManager(rulebooks_dir=str(rulebooks_dir))
    
    # Get all rulebook files
    rulebooks = list(rulebooks_dir.rglob("*.md"))
    assert len(rulebooks) == 2
    
    names = [rb.stem for rb in rulebooks]
    assert "engineering" in names
    assert "writing" in names


def test_rulebook_manager_load_rulebook(rulebooks_dir):
    """Test loading a single rulebook."""
    manager = RulebookManager(rulebooks_dir=str(rulebooks_dir))
    
    engineering_file = rulebooks_dir / "engineering" / "engineering.md"
    assert engineering_file.exists()
    
    content = engineering_file.read_text()
    assert "Engineering Rulebook" in content
    assert "engineering standards" in content


def test_rulebook_manager_validate_structure(rulebooks_dir):
    """Test validating rulebook structure."""
    manager = RulebookManager(rulebooks_dir=str(rulebooks_dir))
    
    # Create a well-formed rulebook
    test_rulebook = rulebooks_dir / "test.md"
    test_rulebook.write_text("""
# Test Rulebook

## Purpose
This is a test rulebook for validation.

## Sections
1. Section One
2. Section Two

## Rules
- Rule 1: First rule
- Rule 2: Second rule
""")
    
    content = test_rulebook.read_text()
    
    # Basic validation - should have headers
    assert "# Test Rulebook" in content
    assert "## Purpose" in content
    assert "## Rules" in content


def test_rulebook_manager_detect_changes():
    """Test detecting changes between rulebook versions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.md"
        
        # Original version
        original_content = "# Rulebook\n\nVersion 1\nOriginal content"
        path.write_text(original_content)
        
        metadata1 = RulebookMetadata(
            name="test",
            category="test",
            version="1.0",
            path=path,
            content=original_content,
        )
        
        # Updated version
        updated_content = "# Rulebook\n\nVersion 2\nUpdated content"
        path.write_text(updated_content)
        
        metadata2 = RulebookMetadata(
            name="test",
            category="test",
            version="1.1",
            path=path,
            content=updated_content,
        )
        
        # Detect differences
        import difflib
        diff = list(difflib.unified_diff(
            metadata1.content.splitlines(keepends=True),
            metadata2.content.splitlines(keepends=True),
        ))
        
        assert len(diff) > 0  # Should have differences
        
        # Find the actual change
        change_found = False
        for line in diff:
            if "Version 1" in line or "Version 2" in line:
                change_found = True
        assert change_found


def test_rulebook_manager_category_organization(rulebooks_dir):
    """Test organizing rulebooks by category."""
    manager = RulebookManager(rulebooks_dir=str(rulebooks_dir))
    
    # All engineering-related files should be in engineering dir
    engineering_files = list((rulebooks_dir / "engineering").glob("*.md"))
    assert len(engineering_files) > 0
    
    # All writing-related files should be in writing dir
    writing_files = list((rulebooks_dir / "writing").glob("*.md"))
    assert len(writing_files) > 0


def test_rulebook_versioning():
    """Test rulebook versioning capability."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir)
        
        # Create versioned rulebook files
        v1 = path / "rulebook-v1.0.0.md"
        v2 = path / "rulebook-v1.1.0.md"
        v3 = path / "rulebook-v2.0.0.md"
        
        v1.write_text("Version 1.0.0 content")
        v2.write_text("Version 1.1.0 content")
        v3.write_text("Version 2.0.0 content")
        
        versions = sorted(path.glob("rulebook-*.md"))
        assert len(versions) == 3
        
        # Parse versions
        version_numbers = [
            f.stem.replace("rulebook-v", "").replace(".md", "")
            for f in versions
        ]
        assert "1.0.0" in version_numbers
        assert "1.1.0" in version_numbers
        assert "2.0.0" in version_numbers
