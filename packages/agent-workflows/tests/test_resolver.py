"""Tests for workflow resolver"""

from pathlib import Path
from unittest.mock import patch

from agent_workflows.resolver import (
    get_global_config_dir,
    get_workflow_extensions,
    list_all_workflows,
    list_bundled_workflows,
    list_global_workflows,
    list_local_workflows,
    resolve_workflow,
)


def test_get_workflow_extensions():
    """Test that all expected extensions are returned"""
    exts = get_workflow_extensions()
    assert ".yml" in exts
    assert ".yaml" in exts
    assert ".agent-workflow.yml" in exts
    assert ".agent-workflow.yaml" in exts


def test_get_global_config_dir():
    """Test that global config dir is returned"""
    config_dir = get_global_config_dir()
    assert isinstance(config_dir, Path)
    assert "siili-agent-workflows" in str(config_dir)


def test_resolve_workflow_from_cwd(tmp_path: Path, monkeypatch):
    """Test resolving workflow from current directory"""
    monkeypatch.chdir(tmp_path)

    # Create a workflow file
    workflow_file = tmp_path / "my-workflow.yml"
    workflow_file.write_text("name: test\njobs: {}\n")

    result = resolve_workflow("my-workflow")
    assert result.path == workflow_file
    assert not result.is_bundled


def test_resolve_workflow_yaml_extension(tmp_path: Path, monkeypatch):
    """Test resolving workflow with .yaml extension"""
    monkeypatch.chdir(tmp_path)

    workflow_file = tmp_path / "my-workflow.yaml"
    workflow_file.write_text("name: test\njobs: {}\n")

    result = resolve_workflow("my-workflow")
    assert result.path == workflow_file


def test_resolve_workflow_agent_workflow_extension(tmp_path: Path, monkeypatch):
    """Test resolving workflow with .agent-workflow.yml extension"""
    monkeypatch.chdir(tmp_path)

    workflow_file = tmp_path / "my-workflow.agent-workflow.yml"
    workflow_file.write_text("name: test\njobs: {}\n")

    result = resolve_workflow("my-workflow")
    assert result.path == workflow_file


def test_resolve_workflow_from_agent_workflows_dir(tmp_path: Path, monkeypatch):
    """Test resolving workflow from .agent_workflows directory"""
    monkeypatch.chdir(tmp_path)

    # Create .agent_workflows directory
    workflows_dir = tmp_path / ".agent_workflows"
    workflows_dir.mkdir()

    workflow_file = workflows_dir / "my-workflow.yml"
    workflow_file.write_text("name: test\njobs: {}\n")

    result = resolve_workflow("my-workflow")
    assert result.path == workflow_file


def test_resolve_workflow_from_global_dir(tmp_path: Path, monkeypatch):
    """Test resolving workflow from global config directory"""
    monkeypatch.chdir(tmp_path)

    # Create a fake global config dir
    global_dir = tmp_path / "global_config"
    global_dir.mkdir()

    workflow_file = global_dir / "my-workflow.yml"
    workflow_file.write_text("name: test\njobs: {}\n")

    with patch("agent_workflows.resolver.get_global_config_dir", return_value=global_dir):
        result = resolve_workflow("my-workflow")
        assert result.path == workflow_file


def test_resolve_workflow_not_found(tmp_path: Path, monkeypatch):
    """Test that non-existent workflow returns None path with searched locations"""
    monkeypatch.chdir(tmp_path)

    result = resolve_workflow("nonexistent-workflow")
    assert result.path is None
    assert len(result.searched_locations) > 0


def test_resolve_workflow_priority(tmp_path: Path, monkeypatch):
    """Test that cwd has priority over .agent_workflows"""
    monkeypatch.chdir(tmp_path)

    # Create workflow in both locations
    cwd_file = tmp_path / "my-workflow.yml"
    cwd_file.write_text("name: cwd\njobs: {}\n")

    workflows_dir = tmp_path / ".agent_workflows"
    workflows_dir.mkdir()
    agent_workflows_file = workflows_dir / "my-workflow.yml"
    agent_workflows_file.write_text("name: agent_workflows\njobs: {}\n")

    result = resolve_workflow("my-workflow")
    assert result.path == cwd_file  # cwd should have priority


def test_list_local_workflows(tmp_path: Path, monkeypatch):
    """Test listing local workflows"""
    monkeypatch.chdir(tmp_path)

    # Create workflows in cwd
    (tmp_path / "workflow1.yml").write_text("name: w1\njobs: {}\n")
    (tmp_path / "workflow2.yaml").write_text("name: w2\njobs: {}\n")

    # Create workflows in .agent_workflows
    workflows_dir = tmp_path / ".agent_workflows"
    workflows_dir.mkdir()
    (workflows_dir / "workflow3.yml").write_text("name: w3\njobs: {}\n")

    local = list_local_workflows()
    assert "workflow1" in local
    assert "workflow2" in local
    assert "workflow3" in local


def test_list_global_workflows(tmp_path: Path):
    """Test listing global workflows"""
    global_dir = tmp_path / "global"
    global_dir.mkdir()
    (global_dir / "global-workflow.yml").write_text("name: global\njobs: {}\n")

    with patch("agent_workflows.resolver.get_global_config_dir", return_value=global_dir):
        global_workflows = list_global_workflows()
        assert "global-workflow" in global_workflows


def test_list_bundled_workflows():
    """Test listing bundled workflows"""
    bundled = list_bundled_workflows()
    # Should have at least the workflows we copied
    assert isinstance(bundled, list)


def test_list_all_workflows(tmp_path: Path, monkeypatch):
    """Test listing all workflows grouped by location"""
    monkeypatch.chdir(tmp_path)

    (tmp_path / "local-workflow.yml").write_text("name: local\njobs: {}\n")

    all_workflows = list_all_workflows()
    assert "local" in all_workflows
    assert "global" in all_workflows
    assert "bundled" in all_workflows
    assert "local-workflow" in all_workflows["local"]
