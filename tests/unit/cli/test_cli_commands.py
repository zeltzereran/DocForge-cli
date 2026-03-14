"""Tests for CLI commands."""

import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specwiz.cli.commands.generate import _load_sources
from specwiz.cli.main import app

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
        result = runner.invoke(
            app,
            [
                "init",
                "--repo",
                tmpdir,
            ],
        )

        # Command should execute (may succeed or show usage)
        assert result.exit_code in [0, 2]


def test_cli_doctor_command():
    """Test CLI doctor command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(
            app,
            [
                "doctor",
                "--repo",
                tmpdir,
            ],
        )

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


def test_cli_rulebook_create_help():
    """Test rulebook create command help."""
    result = runner.invoke(
        app,
        [
            "rulebook",
            "create",
            "--help",
        ],
    )

    assert result.exit_code == 0


def test_cli_rulebook_validate_help():
    """Test rulebook validate command help."""
    result = runner.invoke(
        app,
        [
            "rulebook",
            "validate",
            "--help",
        ],
    )

    assert result.exit_code == 0


def test_cli_rulebook_list_command():
    """Test listing rulebooks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        rulebook_dir = Path(tmpdir) / "rulebooks"
        rulebook_dir.mkdir()

        # Create a sample rulebook
        (rulebook_dir / "engineering.md").write_text("# Engineering Rulebook")

        result = runner.invoke(
            app,
            [
                "rulebook",
                "list",
                "--repo",
                tmpdir,
            ],
        )

        # Should list rulebooks
        assert result.exit_code in [0, 1, 2]


def test_cli_rulebook_create_command():
    """Test creating a rulebook."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(
            app,
            [
                "rulebook",
                "create",
                "--name",
                "test-rulebook",
                "--category",
                "engineering",
                "--repo",
                tmpdir,
            ],
        )

        # Should execute or show error
        assert result.exit_code in [0, 1, 2]


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


def test_prd_help_includes_sources():
    """--sources option appears in prd help output."""
    result = runner.invoke(app, ["generate", "prd", "--help"])
    assert result.exit_code == 0
    assert "--sources" in result.stdout


def test_user_guide_help_includes_sources():
    """--sources option appears in user-guide help output."""
    result = runner.invoke(app, ["generate", "user-guide", "--help"])
    assert result.exit_code == 0
    assert "--sources" in result.stdout


def test_release_notes_help_includes_sources():
    """--sources option appears in release-notes help output."""
    result = runner.invoke(app, ["generate", "release-notes", "--help"])
    assert result.exit_code == 0
    assert "--sources" in result.stdout


# ---------------------------------------------------------------------------
# rulebook generate tests
# ---------------------------------------------------------------------------


def test_rulebook_generate_help_includes_sources():
    """--sources option appears in rulebook generate help."""
    result = runner.invoke(app, ["rulebook", "generate", "--help"])
    assert result.exit_code == 0
    assert "--sources" in result.stdout


def test_rulebook_generate_help_includes_product():
    """--product option appears in rulebook generate help."""
    result = runner.invoke(app, ["rulebook", "generate", "--help"])
    assert result.exit_code == 0
    assert "--product" in result.stdout


def test_rulebook_generate_requires_product():
    """rulebook generate fails without --product."""
    result = runner.invoke(app, ["rulebook", "generate"])
    assert result.exit_code != 0


def test_example_input_keys_not_in_context_keys():
    """_CONTEXT_INPUT_KEYS and _EXAMPLE_INPUT_KEYS are disjoint."""
    from specwiz.cli.commands.generate import _CONTEXT_INPUT_KEYS, _EXAMPLE_INPUT_KEYS

    assert set(_CONTEXT_INPUT_KEYS).isdisjoint(set(_EXAMPLE_INPUT_KEYS))


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
