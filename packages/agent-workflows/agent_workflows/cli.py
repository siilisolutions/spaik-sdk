"""CLI entry point for Agent Workflows.

Usage:
    siili-agent-workflows <workflow-name> [--param value ...]
    siili-agent-workflows --list
    siili-agent-workflows <workflow-name> --validate
"""

import asyncio
import sys
from pathlib import Path

import click
from dotenv import load_dotenv

from .engine import WorkflowExecutionError, run_workflow
from .parser import WorkflowParseError
from .resolver import (
    get_global_config_dir,
    list_all_workflows,
    resolve_workflow,
)


def load_env_hierarchy(env_file: str | None = None) -> None:
    """Load environment variables from multiple sources.

    Order (later overrides earlier):
    1. Global config dir .env
    2. Current directory .env
    3. Explicit --env-file
    """
    global_env = get_global_config_dir() / ".env"
    local_env = Path.cwd() / ".env"

    # Load in order - later overrides earlier
    if global_env.exists():
        load_dotenv(global_env, override=True)

    if local_env.exists():
        load_dotenv(local_env, override=True)

    if env_file:
        load_dotenv(env_file, override=True)


def show_available_workflows() -> None:
    """Display all available workflows grouped by location."""
    workflows = list_all_workflows()

    click.echo("Available workflows:\n")

    if workflows["local"]:
        click.echo("📁 Local (current directory / .agent_workflows/):")
        for name in workflows["local"]:
            click.echo(f"   • {name}")
        click.echo()

    if workflows["global"]:
        global_dir = get_global_config_dir()
        click.echo(f"🌍 Global ({global_dir}):")
        for name in workflows["global"]:
            click.echo(f"   • {name}")
        click.echo()

    if workflows["bundled"]:
        click.echo("📦 Bundled (shipped with package):")
        for name in workflows["bundled"]:
            click.echo(f"   • {name}")
        click.echo()

    if not any(workflows.values()):
        click.echo("   No workflows found.")
        click.echo()
        click.echo(f"💡 Tip: Create a workflow file or place one in {get_global_config_dir()}")


def show_workflow_not_found(name: str, searched: list[str]) -> None:
    """Show helpful error when workflow is not found."""
    click.echo(f"❌ Error: Workflow '{name}' not found.\n", err=True)
    click.echo("Searched in:", err=True)
    for loc in searched:
        click.echo(f"   • {loc}", err=True)
    click.echo()

    # Show available bundled workflows as hints
    workflows = list_all_workflows()
    if workflows["bundled"]:
        click.echo("Available bundled workflows:", err=True)
        for wf in workflows["bundled"]:
            click.echo(f"   • {wf}", err=True)
        click.echo()

    click.echo("Run 'siili-agent-workflows --list' to see all available workflows.", err=True)


def validate_workflow_file(workflow_name: str) -> None:
    """Validate a workflow file without running it."""
    from .dag import DAG, CyclicDependencyError
    from .parser import load_workflow

    result = resolve_workflow(workflow_name)

    if not result.path:
        show_workflow_not_found(workflow_name, result.searched_locations)
        sys.exit(1)

    assert result.path is not None  # for type checker (sys.exit above)
    workflow_path = result.path

    try:
        workflow = load_workflow(workflow_path)
        click.echo(f"✅ Workflow '{workflow['name']}' is valid")
        if result.is_bundled:
            click.echo("   (bundled workflow)")
        else:
            click.echo(f"   Source: {workflow_path}")

        # Check DAG
        deps = {}
        for job_name, job_config in workflow["jobs"].items():
            needs = job_config.get("needs", [])
            if isinstance(needs, str):
                needs = [needs]
            deps[job_name] = needs

        dag = DAG(deps)
        levels = dag.can_run_parallel()

        click.echo(f"📊 {len(workflow['jobs'])} jobs, {len(levels)} execution levels")
        for i, level in enumerate(levels):
            click.echo(f"   Level {i + 1}: {', '.join(level)}")

    except WorkflowParseError as e:
        click.echo(f"❌ Validation failed: {e}", err=True)
        sys.exit(1)
    except CyclicDependencyError as e:
        click.echo(f"❌ Circular dependency: {e}", err=True)
        sys.exit(1)


def run_workflow_by_name(
    workflow_name: str,
    extra_args: list[str],
    workspace: str | None = None,
    set_kv: tuple[str, ...] = (),
    vars_kv: tuple[str, ...] = (),
    dest: str | None = None,
) -> None:
    """Run a workflow by name."""
    result = resolve_workflow(workflow_name)

    if not result.path:
        show_workflow_not_found(workflow_name, result.searched_locations)
        sys.exit(1)

    assert result.path is not None  # for type checker (sys.exit above)
    workflow_path = result.path
    workspace_path = Path(workspace) if workspace else None
    step_overrides = _parse_overrides(set_kv, dest)
    vars_overrides = {**_parse_vars(vars_kv), **_parse_extra_vars(extra_args)}

    try:
        run_result = asyncio.run(
            run_workflow(workflow_path, workspace_path, step_overrides, vars_overrides)
        )

        if run_result["status"] == "success":
            click.echo(f"✅ Workflow '{run_result['workflow_name']}' completed successfully")
            click.echo(f"📊 Duration: {run_result['duration']:.1f}s")
            click.echo(f"📋 Jobs completed: {len(run_result['completed_jobs'])}")
            sys.exit(0)
        else:
            click.echo("❌ Workflow failed", err=True)
            if "failed_jobs" in run_result:
                click.echo(f"💥 Failed jobs: {', '.join(run_result['failed_jobs'])}", err=True)
            sys.exit(1)

    except WorkflowParseError as e:
        click.echo(f"❌ Workflow parse error: {e}", err=True)
        sys.exit(1)
    except WorkflowExecutionError as e:
        click.echo(f"❌ Workflow execution error: {e}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n🛑 Workflow cancelled by user", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"💀 Unexpected error: {e}", err=True)
        sys.exit(1)


@click.command(context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("workflow_name", required=False)
@click.option("--list", "list_workflows", is_flag=True, help="List available workflows")
@click.option("--validate", is_flag=True, help="Validate workflow without running")
@click.option("--env-file", type=click.Path(exists=True), help="Path to .env file")
@click.option(
    "--workspace",
    "-w",
    type=click.Path(exists=True, file_okay=False),
    help="Workspace directory",
)
@click.option(
    "--set",
    "set_kv",
    multiple=True,
    metavar="PLUGIN.KEY=VALUE",
    help="Override step with-values globally, e.g. git/download.dest=out",
)
@click.option(
    "--var",
    "vars_kv",
    multiple=True,
    metavar="KEY=VALUE",
    help="Set/override workflow variables (e.g. myvar=foo)",
)
@click.option("--dest", type=str, default=None, help="Convenience: set git/download.dest")
@click.version_option(version="0.1.0", prog_name="siili-agent-workflows")
@click.pass_context
def cli(
    ctx: click.Context,
    workflow_name: str | None,
    list_workflows: bool,
    validate: bool,
    env_file: str | None,
    workspace: str | None,
    set_kv: tuple[str, ...],
    vars_kv: tuple[str, ...],
    dest: str | None,
) -> None:
    """YAML-driven workflow engine for AI agents.

    Run a workflow by name:

        siili-agent-workflows my-workflow --param value

    List available workflows:

        siili-agent-workflows --list

    Validate a workflow:

        siili-agent-workflows my-workflow --validate
    """
    # Load environment variables
    load_env_hierarchy(env_file)

    # Handle --list flag
    if list_workflows:
        show_available_workflows()
        return

    # Require workflow name for other operations
    if not workflow_name:
        click.echo(ctx.get_help())
        click.echo()
        click.echo("💡 Tip: Run 'siili-agent-workflows --list' to see available workflows.")
        sys.exit(0)

    assert workflow_name is not None  # for type checker (sys.exit above)
    wf_name = workflow_name

    # Handle --validate flag
    if validate:
        validate_workflow_file(wf_name)
        return

    # Default: run the workflow
    run_workflow_by_name(
        workflow_name=wf_name,
        extra_args=ctx.args,
        workspace=workspace,
        set_kv=set_kv,
        vars_kv=vars_kv,
        dest=dest,
    )


def main() -> None:
    """Main entry point."""
    cli()


def _parse_overrides(set_kv: tuple[str, ...], dest: str | None) -> dict:
    """Parse CLI overrides into { plugin: { key: value } } mapping.

    Syntax:
      --set git/download.dest=foo
      --set agents/general.prompt="hello"
      --dest out  (shorthand for git/download.dest)
    """
    overrides: dict[str, dict[str, str]] = {}

    def assign(plugin: str, key: str, value: str) -> None:
        if plugin not in overrides:
            overrides[plugin] = {}
        overrides[plugin][key] = value

    # explicit KEY=VALUE entries
    for pair in set_kv:
        if "=" not in pair:
            continue
        left, value = pair.split("=", 1)
        # left should be plugin.key
        if "." not in left:
            continue
        plugin, key = left.split(".", 1)
        plugin = plugin.strip()
        key = key.strip()
        assign(plugin, key, value)

    if dest:
        assign("git/download", "dest", dest)

    return overrides


def _parse_vars(vars_kv: tuple[str, ...]) -> dict:
    """Parse --var KEY=VALUE pairs to a simple dict."""
    vars_map: dict[str, str] = {}
    for pair in vars_kv:
        if "=" not in pair:
            continue
        key, value = pair.split("=", 1)
        key = key.strip()
        if not key:
            continue
        vars_map[key] = value
    return vars_map


def _parse_extra_vars(args: list[str]) -> dict:
    """Parse unknown CLI args as variable overrides using --key value syntax.

    Examples:
      --myvar project --sub src -> {"myvar": "project", "sub": "src"}
      --flag                    -> {"flag": "true"}
    """
    vars_map: dict[str, str] = {}
    i = 0
    while i < len(args):
        token = args[i]
        if isinstance(token, str) and token.startswith("--") and len(token) > 2:
            key = token[2:]
            value = "true"
            if i + 1 < len(args) and not (
                isinstance(args[i + 1], str) and args[i + 1].startswith("--")
            ):
                value = str(args[i + 1])
                i += 1
            if key:
                vars_map[key] = value
        i += 1
    return vars_map


if __name__ == "__main__":
    main()
