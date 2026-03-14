"""Configuration management for DocForge."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from docforge.core.interfaces.adapters import ConfigAdapter, ConfigSource


class CompositeConfigAdapter(ConfigAdapter):
    """Configuration adapter that merges multiple sources.
    
    Priority order:
    1. Environment variables
    2. .env file (python-dotenv)
    3. docforge.yaml config file
    4. Default fallback values
    """

    def __init__(
        self,
        project_root: Optional[Union[str, Path]] = None,
        env_file: Optional[Union[str, Path]] = None,
    ):
        """Initialize composite config from multiple sources.
        
        Args:
            project_root: Root directory (default: current directory)
            env_file: Path to .env file (default: .env in project root)
        """
        self.project_root = Path(project_root or ".").resolve()
        self.env_file = Path(env_file or self.project_root / ".env")

        # Load sources in priority order
        self._config: Dict[str, tuple[Any, str]] = {}  # (value, source)
        self._load_defaults()
        self._load_env_file()
        self._load_config_file()
        self._load_env_vars()

    def _load_defaults(self) -> None:
        """Load default configuration values."""
        defaults = {
            "project_name": "",
            "project_root": str(self.project_root),
            "llm_model": "claude-3-opus-20240229",
            "llm_provider": "anthropic",
            "temperature": 0.7,
            "max_tokens": 4096,
            "storage_backend": "local",
            "storage_path": str(self.project_root / ".docforge"),
        }
        for key, value in defaults.items():
            self._config[key] = (value, "default")

    def _load_env_file(self) -> None:
        """Load environment variables from .env file."""
        if not self.env_file.exists():
            return

        try:
            from dotenv import dotenv_values

            env_data = dotenv_values(str(self.env_file))
            for key, value in env_data.items():
                if key and value is not None:
                    self._config[key.lower()] = (value, "env_file")
        except ImportError:
            # python-dotenv not available, skip
            pass

    def _load_config_file(self) -> None:
        """Load configuration from docforge.yaml."""
        config_file = self.project_root / "docforge.yaml"
        if not config_file.exists():
            return

        try:
            data = yaml.safe_load(config_file.read_text())
            if data and isinstance(data, dict):
                for key, value in data.items():
                    if key and value is not None:
                        self._config[key.lower()] = (value, "config_file")
        except Exception:
            # Silently skip invalid config files
            pass

    def _load_env_vars(self) -> None:
        """Load environment variables (highest priority)."""
        # Load DOCFORGE_* prefixed variables
        for key, value in os.environ.items():
            if key.startswith("DOCFORGE_"):
                config_key = key[9:].lower()  # Strip DOCFORGE_ prefix
                if config_key:
                    self._config[config_key] = (value, "env_var")

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get config value by key.
        
        Args:
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        key_lower = key.lower()
        if key_lower in self._config:
            return self._config[key_lower][0]
        return default

    def get_source(self, key: str) -> Optional[ConfigSource]:
        """Get config value with source metadata.
        
        Args:
            key: Configuration key
            
        Returns:
            ConfigSource with value and source info, or None
        """
        key_lower = key.lower()
        if key_lower in self._config:
            value, source = self._config[key_lower]
            return ConfigSource(key=key_lower, value=value, source=source)
        return None

    def all_config(self) -> Dict[str, Any]:
        """Get all configuration as dictionary."""
        return {key: value for key, (value, _) in self._config.items()}

    def validate(self) -> List[str]:
        """Validate required configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors: List[str] = []

        # Validate LLM configuration
        if not self.get("ANTHROPIC_API_KEY") and self.get(
            "llm_provider"
        ) == "anthropic":
            errors.append(
                "ANTHROPIC_API_KEY environment variable required for Anthropic provider"
            )

        # Validate project name if needed
        if not self.get("project_name"):
            errors.append("project_name must be configured")

        return errors