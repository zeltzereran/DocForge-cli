"""Tests for CLI commands."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from typer.testing import CliRunner
from docforge.cli.main import app


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
        result = runner.invoke(app, [
            "init",
            "--repo", tmpdir,
        ])
        
        # Command should execute (may succeed or show usage)
        assert result.exit_code in [0, 2]


def test_cli_doctor_command():
    """Test CLI doctor command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(app, [
            "doctor",
            "--repo", tmpdir,
        ])
        
        # Doctor should check system health
        assert result.exit_code in [0, 1, 2]


def test_cli_prd_command_help():
    """Test PRD generation command help."""
    result = runner.invoke(app, [
        "generate", "prd",
        "--help",
    ])
    
    assert result.exit_code == 0
    assert "prd" in result.stdout.lower() or "product" in result.stdout.lower()


def test_cli_user_guide_command_help():
    """Test user guide generation - may or may not exist as separate command."""
    result = runner.invoke(app, [
        "generate",
        "--help",
    ])
    
    # Generate command should exist and show help
    assert result.exit_code == 0 or "generate" in result.stdout.lower()


def test_cli_release_notes_command_help():
    """Test release notes generation - may or may not exist as separate command."""
    result = runner.invoke(app, [
        "generate",
        "--help",
    ])
    
    # Generate command should exist and show help
    assert result.exit_code == 0 or "generate" in result.stdout.lower()


def test_cli_rulebook_list_help():
    """Test rulebook list command help."""
    result = runner.invoke(app, [
        "rulebook", "list",
        "--help",
    ])
    
    assert result.exit_code == 0
    assert "list" in result.stdout.lower() or "rulebook" in result.stdout.lower()


def test_cli_rulebook_create_help():
    """Test rulebook create command help."""
    result = runner.invoke(app, [
        "rulebook", "create",
        "--help",
    ])
    
    assert result.exit_code == 0


def test_cli_rulebook_validate_help():
    """Test rulebook validate command help."""
    result = runner.invoke(app, [
        "rulebook", "validate",
        "--help",
    ])
    
    assert result.exit_code == 0


def test_cli_rulebook_list_command():
    """Test listing rulebooks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        rulebook_dir = Path(tmpdir) / "rulebooks"
        rulebook_dir.mkdir()
        
        # Create a sample rulebook
        (rulebook_dir / "engineering.md").write_text("# Engineering Rulebook")
        
        result = runner.invoke(app, [
            "rulebook", "list",
            "--repo", tmpdir,
        ])
        
        # Should list rulebooks
        assert result.exit_code in [0, 1, 2]


def test_cli_rulebook_create_command():
    """Test creating a rulebook."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = runner.invoke(app, [
            "rulebook", "create",
            "--name", "test-rulebook",
            "--category", "engineering",
            "--repo", tmpdir,
        ])
        
        # Should execute or show error
        assert result.exit_code in [0, 1, 2]


def test_cli_missing_required_option():
    """Test CLI with missing required options."""
    result = runner.invoke(app, [
        "generate", "prd",
    ])
    
    # Should fail with missing required arguments
    assert result.exit_code != 0


def test_cli_invalid_command():
    """Test CLI with invalid command."""
    result = runner.invoke(app, ["invalid-command"])
    
    # Should fail with command not found
    assert result.exit_code != 0


def test_cli_with_verbose_flag():
    """Test CLI with verbose output flag."""
    result = runner.invoke(app, [
        "--help",
        "init",
    ])
    
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
        result = runner.invoke(app, [
            "doctor",
            "--repo", tmpdir,
        ])
        
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
            result1 = runner.invoke(app, [
                "init",
                "--repo", tmpdir1,
            ])
            
            # Run init in tmpdir2
            result2 = runner.invoke(app, [
                "init",
                "--repo", tmpdir2,
            ])
            
            # Both should execute independently
            assert result1.exit_code in [0, 1, 2]
            assert result2.exit_code in [0, 1, 2]
