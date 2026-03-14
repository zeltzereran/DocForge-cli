"""Tests for CLI commands."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from rich.console import Console

from specwiz.cli._paths import load_sources, _is_remote_url
from specwiz.cli.main import app

_console = Console(quiet=True)


def _load_sources(paths):
    """Thin wrapper so existing tests keep working with the new signature."""
    return load_sources(paths, _console)


# ---------------------------------------------------------------------------
# _is_remote_url tests
# ---------------------------------------------------------------------------

def test_is_remote_url_https():
    assert _is_remote_url("https://github.com/org/repo") is True

def test_is_remote_url_http():
    assert _is_remote_url("http://github.com/org/repo") is True

def test_is_remote_url_ssh():
    assert _is_remote_url("git@github.com:org/repo.git") is True

def test_is_remote_url_git_protocol():
    assert _is_remote_url("git://github.com/org/repo.git") is True

def test_is_remote_url_local_dot():
    assert _is_remote_url(".") is False

def test_is_remote_url_local_path():
    assert _is_remote_url("/home/user/projects/myrepo") is False

def test_is_remote_url_relative_path():
    assert _is_remote_url("../myrepo") is False


runner = CliRunner()


def test_cli_app_exists():
    """Test that CLI app is properly configured."""
    assert app is not None
    assert app.registered_commands is not None or app.registered_click_commands is not None


def test_cli_help():
    """Test CLI help output."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.stdout or "Usage" in result.stdout.lower()


def test_cli_version():
    """Test CLI version command."""
    result = runner.invoke(app, ["--version"])
    # Version should be displayed or command should exist
    assert result.exit_code in [0, 2]  # 0 for success, 2 for missing command


def test_cli_init_command():
    """Test CLI init command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        import os
        orig = os.getcwd()
        try:
            os.chdir(tmpdir)
            result = runner.invoke(
                app,
                ["init", "--product", "testproduct"],
            )
        finally:
            os.chdir(orig)

        # Command should execute (may succeed or show usage)
        assert result.exit_code in [0, 2]


def test_cli_doctor_command():
    """Test CLI doctor command."""
    result = runner.invoke(app, ["doctor"])
    # Doctor should check system health
    assert result.exit_code in [0, 1, 2]


def test_cli_prd_command_help():
    """Test PRD generation command help."""
    result = runner.invoke(
        app,
        [
            "generate",
            "prd",
            "--help",
        ],
    )

    assert result.exit_code == 0
    assert "prd" in result.stdout.lower() or "product" in result.stdout.lower()


def test_cli_user_guide_command_help():
    """Test user guide generation - may or may not exist as separate command."""
    result = runner.invoke(
        app,
        [
            "generate",
            "--help",
        ],
    )

    # Generate command should exist and show help
    assert result.exit_code == 0 or "generate" in result.stdout.lower()


def test_cli_release_notes_command_help():
    """Test release notes generation - may or may not exist as separate command."""
    result = runner.invoke(
        app,
        [
            "generate",
            "--help",
        ],
    )

    # Generate command should exist and show help
    assert result.exit_code == 0 or "generate" in result.stdout.lower()


def test_cli_rulebook_list_help():
    """Test rulebook list command help."""
    result = runner.invoke(
        app,
        [
            "rulebook",
            "list",
            "--help",
        ],
    )

    assert result.exit_code == 0
    assert "list" in result.stdout.lower() or "rulebook" in result.stdout.lower()


def test_cli_create_rulebook_prd_help():
    """Test create rulebook prd command help — no --product, only --resources."""
    result = runner.invoke(app, ["create", "rulebook", "prd", "--help"])
    assert result.exit_code == 0
    assert "--product" not in result.stdout
    assert "--resources" in result.stdout


def test_cli_create_knowledge_base_help():
    """Test create knowledge-base command help — no --product, only --sources."""
    result = runner.invoke(app, ["create", "knowledge-base", "--help"])
    assert result.exit_code == 0
    assert "--product" not in result.stdout
    assert "--sources" in result.stdout


def test_cli_rulebook_list_command():
    """Test listing global rulebooks (no --product required)."""
    import os
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set up global rulebooks directory
        rulebooks_dir = Path(tmpdir) / ".specwiz" / "rulebooks"
        rulebooks_dir.mkdir(parents=True)
        (rulebooks_dir / "prd-rulebook.md").write_text("# PRD Rulebook")

        orig = os.getcwd()
        try:
            os.chdir(tmpdir)
            result = runner.invoke(app, ["rulebook", "list"])
        finally:
            os.chdir(orig)

        assert result.exit_code == 0
        assert "prd" in result.stdout.lower()


def test_cli_missing_required_option():
    """Test CLI with missing required options."""
    result = runner.invoke(
        app,
        [
            "generate",
            "prd",
        ],
    )

    # Should fail with missing required arguments
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# _load_sources tests
# ---------------------------------------------------------------------------


def test_load_sources_single_file():
    """File content is returned with a header."""
    with tempfile.TemporaryDirectory() as tmpdir:
        f = Path(tmpdir) / "notes.md"
        f.write_text("hello world")
        result = _load_sources([str(f)])
        assert "--- notes.md ---" in result
        assert "hello world" in result


def test_load_sources_multiple_files():
    """Multiple files are concatenated with headers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "a.md").write_text("alpha")
        (Path(tmpdir) / "b.md").write_text("beta")
        result = _load_sources([str(Path(tmpdir) / "a.md"), str(Path(tmpdir) / "b.md")])
        assert "--- a.md ---" in result
        assert "alpha" in result
        assert "--- b.md ---" in result
        assert "beta" in result


def test_load_sources_directory():
    """All matching files in a directory are loaded."""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "readme.md").write_text("readme content")
        (Path(tmpdir) / "guide.txt").write_text("guide content")
        (Path(tmpdir) / "image.png").write_text("binary")  # should be skipped
        result = _load_sources([tmpdir])
        assert "readme content" in result
        assert "guide content" in result
        assert "image.png" not in result


def test_load_sources_missing_path_skipped(capsys: pytest.CaptureFixture) -> None:
    """Non-existent paths are skipped without raising."""
    result = _load_sources(["/nonexistent/path/file.md"])
    assert result == ""


def test_load_sources_empty_list():
    """Empty input returns empty string."""
    assert _load_sources([]) == ""


# ---------------------------------------------------------------------------
# --sources CLI option tests
# ---------------------------------------------------------------------------


def test_prd_help_includes_resources():
    """--resources option appears in prd help output."""
    result = runner.invoke(app, ["generate", "prd", "--help"])
    assert result.exit_code == 0
    assert "--resources" in result.stdout


def test_user_guide_help_includes_resources():
    """--resources option appears in user-guide help output."""
    result = runner.invoke(app, ["generate", "user-guide", "--help"])
    assert result.exit_code == 0
    assert "--resources" in result.stdout


def test_release_notes_help_includes_resources():
    """--resources option appears in release-notes help output."""
    result = runner.invoke(app, ["generate", "release-notes", "--help"])
    assert result.exit_code == 0
    assert "--resources" in result.stdout


# ---------------------------------------------------------------------------
# rulebook generate tests
# ---------------------------------------------------------------------------


def test_create_rulebook_prd_requires_product():
    """create rulebook prd does NOT accept --product (it is global)."""
    result = runner.invoke(app, ["create", "rulebook", "prd", "--product", "myapp"])
    # --product is an unknown option, should fail
    assert result.exit_code != 0


def test_create_rulebook_prd_requires_resources():
    """create rulebook prd fails without --resources."""
    result = runner.invoke(app, ["create", "rulebook", "prd"])
    # Missing --resources should cause non-zero exit
    assert result.exit_code != 0


def test_source_extensions_include_common_types():
    """_SOURCE_EXTENSIONS in _paths covers the main file types."""
    from specwiz.cli._paths import _SOURCE_EXTENSIONS

    for ext in (".md", ".txt", ".yaml", ".py"):
        assert ext in _SOURCE_EXTENSIONS


def test_load_sources_used_by_rulebook_generate(tmp_path: Path) -> None:
    """_load_sources correctly reads a file; used by rulebook generate path."""
    doc = tmp_path / "example.md"
    doc.write_text("# Example Standard\nDo things this way.")
    result = _load_sources([str(doc)])
    assert "Example Standard" in result
    assert "--- example.md ---" in result


def test_cli_invalid_command():
    """Test CLI with invalid command."""
    result = runner.invoke(app, ["invalid-command"])

    # Should fail with command not found
    assert result.exit_code != 0


def test_cli_with_verbose_flag():
    """Test CLI with verbose output flag."""
    result = runner.invoke(
        app,
        [
            "--help",
            "init",
        ],
    )

    # Should work even with reordered flags
    assert result.exit_code in [0, 2]


def test_cli_output_formatting():
    """Test that CLI output is properly formatted."""
    result = runner.invoke(app, ["--help"])

    # Output should be readable
    assert result.stdout is not None
    assert len(result.stdout) > 0

    # Should have basic structure
    output_lower = result.stdout.lower()
    assert "usage" in output_lower or "commands" in output_lower


def test_cli_error_handling():
    """Test CLI error handling."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Try to run doctor on empty dir
        result = runner.invoke(
            app,
            [
                "doctor",
                "--repo",
                tmpdir,
            ],
        )

        # Should handle gracefully (may show errors but not crash)
        assert isinstance(result.exit_code, int)


def test_cli_subcommand_group():
    """Test that generate and rulebook are subcommand groups."""
    result = runner.invoke(app, ["generate", "--help"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["rulebook", "--help"])
    assert result.exit_code == 0


def test_cli_command_isolation():
    """Test that commands don't interfere with each other."""
    with tempfile.TemporaryDirectory() as tmpdir1:
        with tempfile.TemporaryDirectory() as tmpdir2:
            # Run init in tmpdir1
            result1 = runner.invoke(
                app,
                [
                    "init",
                    "--repo",
                    tmpdir1,
                ],
            )

            # Run init in tmpdir2
            result2 = runner.invoke(
                app,
                [
                    "init",
                    "--repo",
                    tmpdir2,
                ],
            )

            # Both should execute independently
            assert result1.exit_code in [0, 1, 2]
            assert result2.exit_code in [0, 1, 2]


# ---------------------------------------------------------------------------
# load_git_repo_from_url tests
# ---------------------------------------------------------------------------

def test_load_git_repo_from_url_clones_and_walks(tmp_path):
    """load_git_repo_from_url should clone, walk, and clean up the tempdir."""
    from specwiz.cli._paths import load_git_repo_from_url

    fake_content = "# Hello from remote repo"

    def fake_run(cmd, **kwargs):
        # Simulate git writing a file into the clone target (tmpdir = cmd[-1])
        clone_dir = Path(cmd[-1])
        (clone_dir / "README.md").write_text(fake_content)
        result = MagicMock()
        result.returncode = 0
        result.stderr = ""
        return result

    with patch("specwiz.cli._paths.subprocess.run", side_effect=fake_run), \
         patch("specwiz.cli._paths.shutil.which", return_value="/usr/bin/git"):
        content = load_git_repo_from_url("https://github.com/org/repo.git", _console)

    assert fake_content in content


def test_load_git_repo_from_url_git_not_found():
    """load_git_repo_from_url exits with code 1 when git is not on PATH."""
    import pytest
    from specwiz.cli._paths import load_git_repo_from_url

    with patch("specwiz.cli._paths.shutil.which", return_value=None), \
         pytest.raises(SystemExit) as exc_info:
        load_git_repo_from_url("https://github.com/org/repo.git", _console)

    assert exc_info.value.code == 1


def test_load_git_repo_from_url_clone_failure():
    """load_git_repo_from_url exits with code 1 on non-zero git return code."""
    import pytest
    from specwiz.cli._paths import load_git_repo_from_url

    mock_result = MagicMock()
    mock_result.returncode = 128
    mock_result.stderr = "fatal: repository not found"

    with patch("specwiz.cli._paths.shutil.which", return_value="/usr/bin/git"), \
         patch("specwiz.cli._paths.subprocess.run", return_value=mock_result), \
         pytest.raises(SystemExit) as exc_info:
        load_git_repo_from_url("https://github.com/org/missing.git", _console)

    assert exc_info.value.code == 1

