"""Product path resolution and shared file-loading helpers for SpecWiz CLI."""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List

import yaml
from rich.console import Console

_console = Console()

DEFAULT_BASE = ".specwiz"

# Files that make up the product context (checked in order)
_PRODUCT_CONTEXT_FILES = [
    "product-context.md",
    "product-overview.md",
    "architecture.md",
    "data-model.md",
    "glossary.md",
]

_SOURCE_EXTENSIONS = {
    ".md", ".txt", ".yaml", ".yml", ".py", ".ts", ".js",
    ".go", ".java", ".rs", ".json", ".toml",
}

_GIT_EXCLUDE_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "dist", "build", ".specwiz", ".mypy_cache", ".pytest_cache",
}

_GIT_MAX_FILE_CHARS = 50_000    # skip files larger than 50 KB
_GIT_MAX_TOTAL_CHARS = 400_000  # stop scanning after ~400 KB of content


# ──────────────────────────────────────────────
# Path resolution
# ──────────────────────────────────────────────

def get_base_path(cwd: Path) -> Path:
    """Return the configured base storage path (default: .specwiz in cwd)."""
    config_file = cwd / "specwiz.yaml"
    if config_file.exists():
        try:
            data = yaml.safe_load(config_file.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "base_path" in data:
                return cwd / data["base_path"]
        except Exception:
            pass
    return cwd / DEFAULT_BASE


def get_product_path(product: str, cwd: Path) -> Path:
    """Return the product directory path."""
    return get_base_path(cwd) / product


def get_knowledge_base_path(cwd: Path) -> Path:
    """Global knowledge-base path (not product-specific)."""
    return get_base_path(cwd) / "knowledge-base" / "knowledge-base.md"


def get_rulebooks_dir(cwd: Path) -> Path:
    """Global rulebooks directory (not product-specific)."""
    return get_base_path(cwd) / "rulebooks"


def get_rulebook_path(rulebook_type: str, cwd: Path) -> Path:
    """Global rulebook path (not product-specific)."""
    return get_rulebooks_dir(cwd) / f"{rulebook_type}-rulebook.md"


def get_product_context_dir(product: str, cwd: Path) -> Path:
    return get_product_path(product, cwd) / "product-context"


def get_generated_dir(product: str, doc_type: str, cwd: Path) -> Path:
    return get_product_path(product, cwd) / "generated" / doc_type


# ──────────────────────────────────────────────
# Validation helpers (exit on failure)
# ──────────────────────────────────────────────

def validate_product(product: str, cwd: Path) -> Path:
    """Return the product directory or exit with a helpful error."""
    path = get_product_path(product, cwd)
    if not path.exists():
        _console.print(
            f"[red]Product '[bold]{product}[/bold]' not found.[/red]\n"
            f"Run: [cyan]specwiz init --product {product}[/cyan]"
        )
        sys.exit(1)
    return path


def validate_product_context(product: str, cwd: Path) -> str:
    """Return concatenated product-context content or exit with a helpful error."""
    content = load_product_context(product, cwd)
    if not content:
        _console.print(
            f"[red]Product context not found for '[bold]{product}[/bold]'.[/red]\n"
            f"Run: [cyan]specwiz create product-context --product {product} --git .[/cyan]"
        )
        sys.exit(1)
    return content


def validate_rulebook(rulebook_type: str, cwd: Path) -> str:
    """Return rulebook content or exit with a helpful error."""
    path = get_rulebook_path(rulebook_type, cwd)
    if not path.exists():
        _console.print(
            f"[red]Rulebook '[bold]{rulebook_type}[/bold]' not found.[/red]\n"
            f"Run: [cyan]specwiz create rulebook {rulebook_type} --resources <path>[/cyan]"
        )
        sys.exit(1)
    return path.read_text(encoding="utf-8")


# ──────────────────────────────────────────────
# File loading helpers
# ──────────────────────────────────────────────

def load_file(path: Path) -> str:
    """Read a file's content, or return empty string if it doesn't exist."""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def load_knowledge_base(cwd: Path) -> str:
    """Load the global knowledge base (empty string if not yet created)."""
    return load_file(get_knowledge_base_path(cwd))


def _is_remote_url(value: str) -> bool:
    """Return True if value looks like a remote git URL (https, http, git, or SSH shorthand)."""
    return value.startswith(("https://", "http://", "git@", "git://", "ssh://"))


def load_git_repo_from_url(url: str, console: Console) -> str:
    """Shallow-clone a remote git repository into a temp directory, walk it,
    and return the concatenated source file contents.  The temp directory is
    always removed before returning, even on error."""
    if shutil.which("git") is None:
        console.print("[red]Error: 'git' is not on PATH — cannot clone remote repository.[/red]")
        sys.exit(1)

    tmpdir = tempfile.mkdtemp(prefix="specwiz_clone_")
    try:
        console.print(f"[dim]Cloning {url} (shallow) ...[/dim]")
        result = subprocess.run(
            ["git", "clone", "--depth=1", "--quiet", url, tmpdir],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            console.print(
                f"[red]Error: git clone failed.[/red]\n"
                f"{result.stderr.strip()}"
            )
            sys.exit(1)
        return load_git_repo(Path(tmpdir), console)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def load_product_context(product: str, cwd: Path) -> str:
    """Load and concatenate all available product-context files."""
    ctx_dir = get_product_context_dir(product, cwd)
    sections = []
    for name in _PRODUCT_CONTEXT_FILES:
        p = ctx_dir / name
        if p.exists():
            content = p.read_text(encoding="utf-8")
            sections.append(f"--- {name} ---\n{content}")
    return "\n\n".join(sections)


def load_sources(paths: List[str], console: Console) -> str:
    """Read files / directories and return their concatenated content."""
    sections: List[str] = []
    for raw_path in paths:
        p = Path(raw_path)
        if not p.exists():
            console.print(f"[yellow]Warning: path not found, skipping: {raw_path}[/yellow]")
            continue
        if p.is_file():
            files = [p]
        else:
            files = sorted(
                f for f in p.rglob("*")
                if f.is_file() and f.suffix in _SOURCE_EXTENSIONS
            )
        for f in files:
            try:
                content = f.read_text(encoding="utf-8")
                sections.append(f"--- {f.name} ---\n{content}")
            except Exception as exc:
                console.print(f"[yellow]Warning: could not read {f}: {exc}[/yellow]")
    return "\n\n".join(sections)


def load_git_repo(repo_path: Path, console: Console) -> str:
    """Walk a repository directory and return concatenated relevant file contents."""
    sections: List[str] = []
    total_chars = 0

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = sorted(d for d in dirs if d not in _GIT_EXCLUDE_DIRS)
        root_p = Path(root)
        if total_chars >= _GIT_MAX_TOTAL_CHARS:
            break
        for fname in sorted(files):
            fpath = root_p / fname
            if fpath.suffix not in _SOURCE_EXTENSIONS:
                continue
            try:
                size = fpath.stat().st_size
            except Exception:
                continue
            if size > _GIT_MAX_FILE_CHARS:
                continue
            if total_chars >= _GIT_MAX_TOTAL_CHARS:
                break
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                rel = fpath.relative_to(repo_path)
                sections.append(f"--- {rel} ---\n{content}")
                total_chars += len(content)
            except Exception:
                pass

    return "\n\n".join(sections)
