"""Product context extraction and management."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from git import Repo
    GITPYTHON_AVAILABLE = True
except ImportError:
    GITPYTHON_AVAILABLE = False


class ContextFile:
    """Represents an extracted context file."""

    def __init__(self, name: str, content: str, source: str):
        self.name = name
        self.content = content
        self.source = source


class ContextManager:
    """Extracts and manages product context from repositories.
    
    Responsibilities:
    - Extract README, architecture docs, code structure
    - Analyze git history for development patterns
    - Build glossary from codebase terminology
    - Generate structured context files
    """

    def __init__(self, repo_path: Union[str, Path]):
        """Initialize context manager.
        
        Args:
            repo_path: Path to product repository
        """
        self.repo_path = Path(repo_path).resolve()
        self._context_cache: Dict[str, ContextFile] = {}

    def extract_readme(self) -> Optional[ContextFile]:
        """Extract README content.
        
        Returns:
            ContextFile with README content or None
        """
        for readme_name in ["README.md", "README.txt", "README"]:
            readme_path = self.repo_path / readme_name
            if readme_path.exists():
                try:
                    content = readme_path.read_text(encoding="utf-8")
                    return ContextFile(
                        name="README",
                        content=content,
                        source=str(readme_path),
                    )
                except Exception:
                    continue

        return None

    def extract_directory_structure(self, max_depth: int = 3) -> str:
        """Extract repository directory structure.
        
        Args:
            max_depth: Maximum directory depth to traverse
            
        Returns:
            Text representation of directory tree
        """
        lines: List[str] = []

        def walk_tree(path: Path, prefix: str = "", depth: int = 0) -> None:
            if depth > max_depth:
                return

            try:
                items = sorted(path.iterdir())
            except PermissionError:
                return

            # Filter out common unimportant dirs
            ignore_dirs = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"}
            items = [
                i for i in items
                if not (i.is_dir() and i.name in ignore_dirs)
            ]

            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                lines.append(f"{prefix}{current_prefix}{item.name}")

                if item.is_dir():
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    walk_tree(item, next_prefix, depth + 1)

        lines.append(str(self.repo_path.name))
        walk_tree(self.repo_path)

        return "\n".join(lines)

    def extract_git_history(self, limit: int = 50) -> Optional[str]:
        """Extract recent git history.
        
        Args:
            limit: Number of commits to extract
            
        Returns:
            Git log as string or None if not a git repo
        """
        if not GITPYTHON_AVAILABLE:
            return None

        try:
            repo = Repo(self.repo_path)
            commits = list(repo.iter_commits(max_count=limit))

            lines = [f"# Recent Git History ({len(commits)} commits)\n"]
            for commit in commits:
                lines.append(f"- {commit.hexsha[:7]}: {commit.message.splitlines()[0]}")

            return "\n".join(lines)
        except Exception:
            return None

    def extract_package_metadata(self) -> Dict[str, Any]:
        """Extract package/project metadata.
        
        Returns:
            Dictionary of metadata (name, version, description, etc.)
        """
        metadata: Dict[str, Any] = {}

        # Check for Python project
        pyproject = self.repo_path / "pyproject.toml"
        if pyproject.exists():
            try:
                import tomllib
                content = tomllib.loads(pyproject.read_text())
                if "project" in content:
                    proj = content["project"]
                    metadata["name"] = proj.get("name", "")
                    metadata["version"] = proj.get("version", "")
                    metadata["description"] = proj.get("description", "")
            except Exception:
                pass

        # Check for Node.js project
        package_json = self.repo_path / "package.json"
        if package_json.exists():
            try:
                import json
                content = json.loads(package_json.read_text())
                metadata["name"] = content.get("name", "")
                metadata["version"] = content.get("version", "")
                metadata["description"] = content.get("description", "")
            except Exception:
                pass

        return metadata

    async def generate_context_files(self) -> Dict[str, ContextFile]:
        """Generate all context files.
        
        Returns:
            Dictionary of context files by name
        """
        context_files: Dict[str, ContextFile] = {}

        # Extract README
        readme = self.extract_readme()
        if readme:
            context_files["readme"] = readme

        # Extract directory structure
        tree_content = self.extract_directory_structure()
        context_files["directory_structure"] = ContextFile(
            name="Directory Structure",
            content=tree_content,
            source="analyzed",
        )

        # Extract git history
        git_hist = self.extract_git_history()
        if git_hist:
            context_files["git_history"] = ContextFile(
                name="Git History",
                content=git_hist,
                source="git",
            )

        # Extract metadata
        metadata = self.extract_package_metadata()
        context_files["metadata"] = ContextFile(
            name="Package Metadata",
            content=str(metadata),
            source="package_files",
        )

        return context_files

    def get_context(self) -> str:
        """Get full context as formatted string.
        
        Returns:
            Complete context information
        """
        lines: List[str] = []

        lines.append("# Product Context\n")

        # Get metadata
        metadata = self.extract_package_metadata()
        if metadata:
            lines.append("## Project Information\n")
            for key, value in metadata.items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")

        # Get README
        readme = self.extract_readme()
        if readme:
            lines.append("## README\n")
            lines.append(readme.content)
            lines.append("")

        # Get directory structure
        lines.append("## Directory Structure\n")
        lines.append("```")
        lines.append(self.extract_directory_structure())
        lines.append("```\n")

        # Get git history
        git_hist = self.extract_git_history()
        if git_hist:
            lines.append(f"## Git History\n{git_hist}\n")

        return "\n".join(lines)
