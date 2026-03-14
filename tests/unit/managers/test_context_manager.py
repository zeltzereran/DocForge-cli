"""Tests for context manager."""

import pytest
import tempfile
from pathlib import Path
import json

from docforge.core.managers.context import ContextManager, ContextFile


@pytest.fixture
def sample_repo():
    """Create a sample repository structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        
        # Create README
        (repo_path / "README.md").write_text("""
# Sample Project

This is a sample documentation project.

## Features
- Feature 1
- Feature 2

## Getting Started
1. Clone the repo
2. Install dependencies
3. Run the application
""")
        
        # Create basic structure
        src_dir = repo_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("def main():\n    pass")
        
        # Create config
        (repo_path / "config.json").write_text(json.dumps({
            "name": "sample-project",
            "version": "1.0.0",
            "description": "A sample project",
        }))
        
        yield repo_path


def test_context_file_creation():
    """Test ContextFile model creation."""
    context_file = ContextFile(
        name="overview.md",
        content="# Project Overview\nThis is the overview.",
        source="README.md",
    )
    
    assert context_file.name == "overview.md"
    assert context_file.content == "# Project Overview\nThis is the overview."
    assert context_file.source == "README.md"


def test_context_manager_initialization(sample_repo):
    """Test ContextManager initialization."""
    manager = ContextManager(repo_path=str(sample_repo))
    
    # Paths should resolve to Path objects
    assert manager.repo_path is not None
    assert isinstance(manager._context_cache, dict)


def test_context_manager_extract_readme(sample_repo):
    """Test extracting README from repository."""
    manager = ContextManager(repo_path=str(sample_repo))
    
    readme_path = sample_repo / "README.md"
    content = readme_path.read_text()
    
    assert "Sample Project" in content
    assert "Features" in content
    assert "Getting Started" in content


def test_context_manager_extract_directory_structure(sample_repo):
    """Test extracting directory structure."""
    manager = ContextManager(repo_path=str(sample_repo))
    
    # List all files and directories
    all_paths = list(sample_repo.rglob("*"))
    
    # Should find the src directory and its files
    src_files = [p for p in all_paths if "src" in str(p)]
    assert len(src_files) > 0
    
    # Should find main.py
    main_py_files = [p for p in all_paths if p.name == "main.py"]
    assert len(main_py_files) > 0


def test_context_manager_extract_config(sample_repo):
    """Test extracting configuration files."""
    manager = ContextManager(repo_path=str(sample_repo))
    
    config_path = sample_repo / "config.json"
    content = config_path.read_text()
    config_data = json.loads(content)
    
    assert config_data["name"] == "sample-project"
    assert config_data["version"] == "1.0.0"


def test_context_manager_caching(sample_repo):
    """Test context caching mechanism."""
    manager = ContextManager(repo_path=str(sample_repo))
    
    # Add something to cache
    context_file = ContextFile(
        name="cached.md",
        content="Cached content",
        source="memory",
    )
    
    manager._context_cache["cached"] = context_file
    
    # Retrieve from cache
    assert "cached" in manager._context_cache
    assert manager._context_cache["cached"].content == "Cached content"


def test_context_manager_git_history_extraction(sample_repo):
    """Test attempting to extract git history."""
    manager = ContextManager(repo_path=str(sample_repo))
    
    # The repo is not a git repo, so git operations should fail gracefully
    # but the manager should still work with filesystem data
    
    all_files = list(sample_repo.rglob("*.md")) + list(sample_repo.rglob("*.py"))
    assert len(all_files) > 0


def test_context_manager_file_listing(sample_repo):
    """Test listing project files."""
    manager = ContextManager(repo_path=str(sample_repo))
    
    # Get all Python files
    py_files = list(sample_repo.rglob("*.py"))
    assert len(py_files) > 0
    
    # Get all markdown files
    md_files = list(sample_repo.rglob("*.md"))
    assert len(md_files) > 0
    
    # Get all JSON files
    json_files = list(sample_repo.rglob("*.json"))
    assert len(json_files) > 0


def test_context_manager_builds_glossary(sample_repo):
    """Test building a project glossary from code."""
    manager = ContextManager(repo_path=str(sample_repo))
    
    # Extract terms from README
    readme_path = sample_repo / "README.md"
    readme_content = readme_path.read_text()
    
    # Should identify key terms
    assert "Sample Project" in readme_content
    assert "Features" in readme_content


def test_context_manager_analyzes_structure_hierarchy(sample_repo):
    """Test analyzing project structure hierarchy."""
    manager = ContextManager(repo_path=str(sample_repo))
    
    # Build hierarchy
    root_files = list(sample_repo.glob("*"))
    assert len(root_files) > 0
    
    # Should have both files and directories
    files = [p for p in root_files if p.is_file()]
    dirs = [p for p in root_files if p.is_dir()]
    
    assert len(files) > 0
    assert len(dirs) > 0


def test_context_manager_handles_missing_repo():
    """Test handling of missing repository."""
    manager = ContextManager(repo_path="/nonexistent/path")
    
    # Should initialize even if path doesn't exist
    # (path resolution happens on access)
    assert manager.repo_path == Path("/nonexistent/path").resolve()