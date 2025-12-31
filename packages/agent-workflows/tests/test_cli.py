"""Tests for CLI"""

from pathlib import Path

from click.testing import CliRunner

from agent_workflows.cli import cli


def test_cli_help():
    """Test --help flag"""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "YAML-driven workflow engine" in result.output


def test_cli_version():
    """Test --version flag"""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "siili-agent-workflows" in result.output


def test_cli_list_flag():
    """Test --list flag shows available workflows"""
    runner = CliRunner()
    result = runner.invoke(cli, ["--list"])
    assert result.exit_code == 0
    assert "Available workflows" in result.output


def test_cli_no_args_shows_help():
    """Test that no args shows help"""
    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert "YAML-driven workflow engine" in result.output


def test_cli_workflow_not_found():
    """Test error message when workflow not found"""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["nonexistent-workflow"])
        assert result.exit_code == 1
        assert "not found" in result.output


def test_cli_validate_flag(tmp_path: Path):
    """Test --validate flag"""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a valid workflow
        Path("test-workflow.yml").write_text(
            "name: test\njobs:\n  build:\n    steps:\n      - uses: test@v1\n"
        )

        result = runner.invoke(cli, ["test-workflow", "--validate"])
        assert result.exit_code == 0
        assert "is valid" in result.output


def test_cli_validate_invalid_workflow(tmp_path: Path):
    """Test --validate flag with invalid workflow"""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create an invalid workflow (missing jobs)
        Path("invalid-workflow.yml").write_text("name: invalid\n")

        result = runner.invoke(cli, ["invalid-workflow", "--validate"])
        assert result.exit_code == 1
        assert "Validation failed" in result.output or "error" in result.output.lower()


def test_cli_env_file_loading(tmp_path: Path):
    """Test --env-file option"""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create an env file
        Path(".env.test").write_text("TEST_VAR=test_value\n")

        # Just test that the option is accepted (workflow won't exist but that's ok)
        result = runner.invoke(cli, ["--env-file", ".env.test", "--list"])
        assert result.exit_code == 0
