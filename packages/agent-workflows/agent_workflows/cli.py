"""CLI entry point for Agent Workflows"""

import asyncio
import sys
from pathlib import Path
import click
from dotenv import load_dotenv
from .engine import run_workflow, WorkflowExecutionError
from .parser import WorkflowParseError


@click.group()
@click.version_option(version="0.1.0", prog_name="agent-workflow")
def cli():
    """Agent Workflows - YAML-driven workflow engine for AI agents"""
    pass


@cli.command()
@click.option('--file', '-f', default='.agent-workflow.yml', help='Workflow file to run')
@click.option('--workspace', '-w', type=click.Path(exists=True, file_okay=False), 
              help='Workspace directory')
def run(file: str, workspace: str):
    """Run a workflow"""
    workflow_path = Path(file)
    workspace_path = Path(workspace) if workspace else None
    
    if not workflow_path.exists():
        click.echo(f"❌ Workflow file not found: {workflow_path}", err=True)
        sys.exit(1)
    
    try:
        result = asyncio.run(run_workflow(workflow_path, workspace_path))
        
        if result['status'] == 'success':
            click.echo(f"✅ Workflow '{result['workflow_name']}' completed successfully")
            click.echo(f"📊 Duration: {result['duration']:.1f}s")
            click.echo(f"📋 Jobs completed: {len(result['completed_jobs'])}")
            sys.exit(0)
        else:
            click.echo(f"❌ Workflow failed", err=True)
            if 'failed_jobs' in result:
                click.echo(f"💥 Failed jobs: {', '.join(result['failed_jobs'])}", err=True)
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


@cli.command()
@click.option('--limit', '-l', default=10, help='Number of recent runs to show')
def history(limit: int):
    """Show workflow run history"""
    history_dir = Path.cwd() / '.agent-workflows' / 'history'
    
    if not history_dir.exists():
        click.echo("📭 No workflow history found")
        return
    
    import json
    from datetime import datetime
    
    # Get recent runs
    run_files = sorted(history_dir.glob('*.json'), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not run_files:
        click.echo("📭 No workflow runs found")
        return
    
    click.echo("📚 Recent workflow runs:")
    click.echo()
    
    for run_file in run_files[:limit]:
        try:
            with open(run_file) as f:
                run_data = json.load(f)
            
            status_icon = "✅" if run_data['status'] == 'success' else "❌"
            duration = run_data.get('duration', 0)
            start_time = datetime.fromtimestamp(run_data['start_time']).strftime("%Y-%m-%d %H:%M:%S")
            
            click.echo(f"{status_icon} {run_data['workflow_name']} ({run_data['run_id']})")
            click.echo(f"   📅 {start_time} | ⏱️  {duration:.1f}s")
            
            if run_data['status'] == 'success':
                completed = len(run_data.get('completed_jobs', []))
                click.echo(f"   📋 {completed} jobs completed")
            else:
                failed = run_data.get('failed_jobs', [])
                click.echo(f"   💥 Failed jobs: {', '.join(failed)}")
            
            click.echo()
            
        except Exception as e:
            click.echo(f"⚠️  Error reading {run_file.name}: {e}")


@cli.command()
@click.argument('workflow_file', type=click.Path(exists=True))
def validate(workflow_file: str):
    """Validate a workflow file"""
    from .parser import load_workflow
    from .dag import DAG, CyclicDependencyError
    
    try:
        workflow = load_workflow(Path(workflow_file))
        click.echo(f"✅ Workflow '{workflow['name']}' is valid")
        
        # Check DAG
        deps = {}
        for job_name, job_config in workflow['jobs'].items():
            needs = job_config.get('needs', [])
            if isinstance(needs, str):
                needs = [needs]
            deps[job_name] = needs
        
        dag = DAG(deps)
        levels = dag.can_run_parallel()
        
        click.echo(f"📊 {len(workflow['jobs'])} jobs, {len(levels)} execution levels")
        for i, level in enumerate(levels):
            click.echo(f"   Level {i+1}: {', '.join(level)}")
            
    except WorkflowParseError as e:
        click.echo(f"❌ Validation failed: {e}", err=True)
        sys.exit(1)
    except CyclicDependencyError as e:
        click.echo(f"❌ Circular dependency: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point"""
    cli()


if __name__ == '__main__':
    load_dotenv("../agent-sdk/.env")
    # import os
    # print(os.getenv("DEFAULT_MODEL"))
    main()