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


def show_getting_started() -> None:
    """Show getting started guide when no workflow is specified."""
    global_dir = get_global_config_dir()
    global_env = global_dir / ".env"

    click.echo()
    click.echo("🚀 SIILI AGENT WORKFLOWS")
    click.echo("=" * 50)
    click.echo()
    click.echo("Run workflows by name:")
    click.echo("  siili-agent-workflows <workflow-name> [options]")
    click.echo()
    click.echo("─" * 50)
    click.echo("📦 BUNDLED WORKFLOWS")
    click.echo("─" * 50)

    workflows = list_all_workflows()
    if workflows["bundled"]:
        for wf in workflows["bundled"]:
            click.echo(f"  • {wf}")
    click.echo()

    click.echo("─" * 50)
    click.echo("🔑 API KEYS SETUP")
    click.echo("─" * 50)
    click.echo(f"Create: {global_env}")
    click.echo()
    click.echo("  OPENAI_API_KEY=sk-...")
    click.echo("  ANTHROPIC_API_KEY=sk-ant-...")
    click.echo()

    click.echo("─" * 50)
    click.echo("📁 WORKFLOW LOCATIONS (searched in order)")
    click.echo("─" * 50)
    click.echo("  1. ./workflow-name.yml")
    click.echo("  2. ./.agent_workflows/workflow-name.yml")
    click.echo(f"  3. {global_dir}/workflow-name.yml")
    click.echo("  4. Bundled (shipped with package)")
    click.echo()

    click.echo("─" * 50)
    click.echo("📝 CREATE A WORKFLOW")
    click.echo("─" * 50)
    click.echo("  my-workflow.yml:")
    click.echo()
    click.echo("  name: my-workflow")
    click.echo("  jobs:")
    click.echo("    main:")
    click.echo("      steps:")
    click.echo("        - uses: terminal/run")
    click.echo("          with:")
    click.echo('            command: echo "Hello!"')
    click.echo("        - uses: agents/claude_code")
    click.echo("          with:")
    click.echo('            prompt: "Do something"')
    click.echo()

    click.echo("─" * 50)
    click.echo("🔌 AVAILABLE PLUGINS")
    click.echo("─" * 50)
    click.echo("  terminal/run       - Run shell commands")
    click.echo("  terminal/script    - Run script files")
    click.echo("  git/download       - Clone/download repos")
    click.echo("  git/push           - Push changes")
    click.echo("  agents/claude_code - Claude Code CLI")
    click.echo("  agents/general     - General LLM agent")
    click.echo("  agents/structured  - Structured JSON responses")
    click.echo("  audio/stt          - Speech-to-text")
    click.echo("  audio/tts          - Text-to-speech")
    click.echo()

    click.echo("Try: siili-agent-workflows --list")
    click.echo("     siili-agent-workflows --help")
    click.echo()


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


def show_env_hint() -> None:
    """Show hint about where to put API keys."""
    global_dir = get_global_config_dir()
    global_env = global_dir / ".env"
    click.echo()
    click.echo("💡 To set API keys, create a .env file at one of:", err=True)
    click.echo(f"   • {global_env} (global, recommended)", err=True)
    click.echo("   • ./.env (current directory)", err=True)
    click.echo()
    click.echo("   Example .env contents:", err=True)
    click.echo("   OPENAI_API_KEY=sk-...", err=True)
    click.echo("   ANTHROPIC_API_KEY=sk-ant-...", err=True)


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

    # Show where env files are loaded from
    global_dir = get_global_config_dir()
    click.echo(f"📁 Config: {global_dir}")

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
        error_msg = str(e)
        click.echo(f"❌ Workflow execution error: {e}", err=True)
        # Check for common API key errors
        if "API_KEY" in error_msg or "api_key" in error_msg.lower():
            show_env_hint()
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n🛑 Workflow cancelled by user", err=True)
        sys.exit(130)
    except Exception as e:
        error_msg = str(e)
        click.echo(f"💀 Unexpected error: {e}", err=True)
        # Check for common API key errors
        if "API_KEY" in error_msg or "api_key" in error_msg.lower():
            show_env_hint()
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

    \b
    QUICK START
    ───────────
    siili-agent-workflows --list              # See available workflows
    siili-agent-workflows speech-input        # Run a bundled workflow
    siili-agent-workflows my-workflow --var key=value

    \b
    WORKFLOW FORMAT (my-workflow.yml)
    ─────────────────────────────────
    name: my-workflow
    vars:
      default_value: hello
    jobs:
      main:
        steps:
          - uses: terminal/run
            with:
              command: echo "${{ default_value }}"
          - uses: agents/claude_code
            with:
              prompt: "Do something"
              cwd: "."

    \b
    WORKFLOW LOCATIONS (searched in order)
    ──────────────────────────────────────
    1. ./my-workflow.yml (current directory)
    2. ./.agent_workflows/my-workflow.yml
    3. ~/.config/siili-agent-workflows/my-workflow.yml (global)
    4. Bundled workflows (shipped with package)

    \b
    AVAILABLE PLUGINS
    ─────────────────
    terminal/run       - Run shell commands
    terminal/script    - Run script files
    git/download       - Clone/download from repos
    git/push           - Push changes
    agents/claude_code - Claude Code CLI agent
    agents/general     - General LLM agent
    agents/structured  - Structured JSON responses
    audio/stt          - Speech-to-text (record & transcribe)
    audio/tts          - Text-to-speech

    \b
    API KEYS
    ────────
    Create ~/.config/siili-agent-workflows/.env with:
      OPENAI_API_KEY=sk-...
      ANTHROPIC_API_KEY=sk-ant-...

    Or use .env in current directory, or --env-file option.
    """
    # Load environment variables
    load_env_hierarchy(env_file)

    # Handle --list flag
    if list_workflows:
        show_available_workflows()
        return

    # Require workflow name for other operations
    if not workflow_name:
        show_getting_started()
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
