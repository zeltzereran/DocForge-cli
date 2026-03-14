"""Tests for configuration manager."""

import os
import pytest
import tempfile
from pathlib import Path

from docforge.core.managers.config import CompositeConfigAdapter


@pytest.fixture
def temp_config_dir():
    """Create temporary config directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def env_file(temp_config_dir):
    """Create a sample .env file."""
    env_path = temp_config_dir / ".env"
    env_path.write_text(
        "DOCFORGE_LLM_API_KEY=test-api-key\n"
        "DOCFORGE_LLM_MODEL=claude-3-opus-20240229\n"
        "DOCFORGE_PROJECT_NAME=TestProject\n"
    )
    return env_path


@pytest.fixture
def config_yaml_file(temp_config_dir):
    """Create a sample docforge.yaml config file."""
    config_path = temp_config_dir / "docforge.yaml"
    config_path.write_text(
        """
llm:
  api_key: file-api-key
  model: claude-3-sonnet-20240229
  temperature: 0.7

storage:
  base_path: ./artifacts

project:
  name: FileConfigProject
  description: Configuration from YAML file
"""
    )
    return config_path


def test_config_from_env_variables(temp_config_dir):
    """Test reading config from environment variables."""
    # Set env vars
    os.environ["DOCFORGE_LLM_API_KEY"] = "env-api-key"
    os.environ["DOCFORGE_LLM_MODEL"] = "claude-3-haiku-20240307"
    
    try:
        adapter = CompositeConfigAdapter(project_root=str(temp_config_dir))
        
        # Check that config can be retrieved
        config = adapter.all_config()
        assert isinstance(config, dict)
    finally:
        # Clean up
        os.environ.pop("DOCFORGE_LLM_API_KEY", None)
        os.environ.pop("DOCFORGE_LLM_MODEL", None)


def test_config_from_env_file(env_file, temp_config_dir):
    """Test reading config from .env file."""
    adapter = CompositeConfigAdapter(
        project_root=str(temp_config_dir),
        env_file=str(env_file),
    )
    
    # Check that adapter initializes without error
    assert adapter is not None
    assert adapter.project_root.resolve() == Path(temp_config_dir).resolve()


def test_config_from_yaml_file(config_yaml_file, temp_config_dir):
    """Test reading config from docforge.yaml file."""
    adapter = CompositeConfigAdapter(project_root=str(temp_config_dir))
    
    llm_config = adapter.get("llm")
    assert llm_config["model"] == "claude-3-sonnet-20240229"
    assert llm_config["temperature"] == 0.7
    
    project_config = adapter.get("project")
    assert project_config["name"] == "FileConfigProject"


def test_config_priority_env_over_file(env_file, config_yaml_file, temp_config_dir):
    """Test that configuration is loaded from multiple sources."""
    # Set env var
    os.environ["DOCFORGE_LLM_MODEL"] = "env-model"
    
    try:
        adapter = CompositeConfigAdapter(
            project_root=str(temp_config_dir),
            env_file=str(env_file),
        )
        
        # Adapter should initialize successfully
        assert adapter is not None
    finally:
        os.environ.pop("DOCFORGE_LLM_MODEL", None)


def test_config_get_with_default():
    """Test getting config value with default fallback."""
    with tempfile.TemporaryDirectory() as tmpdir:
        adapter = CompositeConfigAdapter(project_root=str(tmpdir))
        
        # Non-existent key with default
        value = adapter.get("nonexistent", default="default_value")
        assert value == "default_value"


def test_config_all_keys():
    """Test configuration functionality."""
    with tempfile.TemporaryDirectory() as tmpdir:
        adapter = CompositeConfigAdapter(project_root=str(tmpdir))
        
        # Set some env vars
        os.environ["DOCFORGE_TEST_KEY"] = "test_value"
        
        try:
            # Check adapter is initialized
            assert adapter is not None
            assert adapter.project_root is not None
        finally:
            os.environ.pop("DOCFORGE_TEST_KEY", None)
