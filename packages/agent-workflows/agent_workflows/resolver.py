"""Workflow file resolution logic.

Resolves workflow names to file paths by searching multiple locations:
1. Current directory (name.yml, name.yaml, name.agent-workflow.yml, etc.)
2. Local .agent_workflows/ directory
3. Global config directory (~/.config/siili-agent-workflows/ on Linux/Mac)
4. Bundled workflows shipped with the package
"""

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from platformdirs import user_config_dir

APP_NAME = "siili-agent-workflows"


@dataclass
class SearchResult:
    """Result of workflow resolution."""

    path: Path | None
    searched_locations: list[str]
    is_bundled: bool = False


def get_global_config_dir() -> Path:
    """Get the global config directory for storing workflows and .env files."""
    return Path(user_config_dir(APP_NAME))


def get_workflow_extensions() -> list[str]:
    """Get all supported workflow file extensions."""
    return [
        ".yml",
        ".yaml",
        ".agent-workflow.yml",
        ".agent-workflow.yaml",
    ]


def resolve_workflow(name: str) -> SearchResult:
    """Resolve a workflow name to a file path.

    Searches in order:
    1. Current directory with various extensions
    2. .agent_workflows/ subdirectory
    3. Global config directory
    4. Bundled workflows in package

    Args:
        name: Workflow name (without extension)

    Returns:
        SearchResult with path (if found) and list of searched locations
    """
    searched: list[str] = []
    extensions = get_workflow_extensions()
    cwd = Path.cwd()
    global_dir = get_global_config_dir()

    # 1. Current directory
    for ext in extensions:
        candidate = cwd / f"{name}{ext}"
        searched.append(str(candidate))
        if candidate.exists():
            return SearchResult(path=candidate, searched_locations=searched)

    # 2. Local .agent_workflows/ directory
    local_workflows_dir = cwd / ".agent_workflows"
    for ext in extensions:
        candidate = local_workflows_dir / f"{name}{ext}"
        searched.append(str(candidate))
        if candidate.exists():
            return SearchResult(path=candidate, searched_locations=searched)

    # 3. Global config directory
    for ext in extensions:
        candidate = global_dir / f"{name}{ext}"
        searched.append(str(candidate))
        if candidate.exists():
            return SearchResult(path=candidate, searched_locations=searched)

    # 4. Bundled workflows
    bundled_path = get_bundled_workflow(name)
    searched.append(f"(bundled workflow '{name}')")
    if bundled_path:
        return SearchResult(path=bundled_path, searched_locations=searched, is_bundled=True)

    return SearchResult(path=None, searched_locations=searched)


def get_bundled_workflow(name: str) -> Path | None:
    """Get a bundled workflow file from the package.

    Args:
        name: Workflow name (without extension)

    Returns:
        Path to the bundled workflow file, or None if not found
    """
    try:
        pkg = files("agent_workflows.workflows")
    except (ModuleNotFoundError, TypeError):
        return None

    for ext in get_workflow_extensions():
        try:
            filename = f"{name}{ext}"
            res = pkg.joinpath(filename)
            # Check if it's a real file (works for both installed packages and editable installs)
            if hasattr(res, "is_file") and res.is_file():
                # For importlib.resources, we need to get the actual path
                # This works for both regular and editable installs
                return Path(str(res))
        except (FileNotFoundError, TypeError, AttributeError):
            continue

    return None


def list_bundled_workflows() -> list[str]:
    """List all bundled workflow names.

    Returns:
        List of workflow names (without extensions)
    """
    workflows: set[str] = set()

    try:
        pkg = files("agent_workflows.workflows")
        # Iterate over files in the package
        for item in pkg.iterdir():
            name = str(item.name)
            # Strip known extensions to get workflow name
            for ext in get_workflow_extensions():
                if name.endswith(ext):
                    workflow_name = name[: -len(ext)]
                    workflows.add(workflow_name)
                    break
    except (ModuleNotFoundError, TypeError, AttributeError):
        pass

    return sorted(workflows)


def list_global_workflows() -> list[str]:
    """List workflows in the global config directory.

    Returns:
        List of workflow names (without extensions)
    """
    workflows: set[str] = set()
    global_dir = get_global_config_dir()

    if not global_dir.exists():
        return []

    for ext in get_workflow_extensions():
        for path in global_dir.glob(f"*{ext}"):
            workflow_name = path.name[: -len(ext)]
            workflows.add(workflow_name)

    return sorted(workflows)


def list_local_workflows() -> list[str]:
    """List workflows in current directory and .agent_workflows/.

    Returns:
        List of workflow names (without extensions)
    """
    workflows: set[str] = set()
    cwd = Path.cwd()
    local_dir = cwd / ".agent_workflows"

    for search_dir in [cwd, local_dir]:
        if not search_dir.exists():
            continue
        for ext in get_workflow_extensions():
            for path in search_dir.glob(f"*{ext}"):
                workflow_name = path.name[: -len(ext)]
                workflows.add(workflow_name)

    return sorted(workflows)


def list_all_workflows() -> dict[str, list[str]]:
    """List all available workflows grouped by location.

    Returns:
        Dict with keys 'local', 'global', 'bundled' mapping to workflow name lists
    """
    return {
        "local": list_local_workflows(),
        "global": list_global_workflows(),
        "bundled": list_bundled_workflows(),
    }
