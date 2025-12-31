"""Core workflow execution engine"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Set

from .dag import DAG
from .parser import get_job_dependencies, load_workflow
from .plugins import load_plugin


class WorkflowExecutionError(Exception):
    """Raised when workflow execution fails"""
    pass


class WorkflowEngine:
    """Executes workflows with parallel job support"""
    
    def __init__(
        self,
        workspace: Optional[Path] = None,
        step_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
        vars_overrides: Optional[Dict[str, Any]] = None,
    ):
        self.workspace = workspace or Path.cwd()
        self.history_dir = self.workspace / '.agent-workflows' / 'history'
        self.history_dir.mkdir(parents=True, exist_ok=True)
        # Step-level overrides keyed by plugin path, e.g. {"git/download": {"dest": "..."}}
        self.step_overrides: Dict[str, Dict[str, Any]] = step_overrides or {}
        # global variables for interpolation (filled per run)
        self.global_vars: Dict[str, Any] = {}
        self.vars_overrides: Dict[str, Any] = vars_overrides or {}
    
    async def run(self, workflow_path: Path) -> Dict[str, Any]:
        """Execute a workflow and return run metadata"""
        start_time = time.time()
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Load and parse workflow
            workflow = load_workflow(workflow_path)
            deps = get_job_dependencies(workflow['jobs'])
            dag = DAG(deps)
            
            # Create run context
            run_metadata: Dict[str, Any] = {
                'run_id': run_id,
                'workflow_name': workflow['name'],
                'start_time': start_time,
                'workspace': str(self.workspace),
                'status': 'running',
                'jobs': {}
            }
            
            # capture global vars for interpolation (workflow vars + CLI overrides)
            self.global_vars = dict(workflow.get('vars', {}))
            if self.vars_overrides:
                self.global_vars.update(self.vars_overrides)

            self._log(f"🚀 Starting workflow: {workflow['name']}")
            
            # Execute jobs in parallel where possible
            completed_jobs: Set[str] = set()
            failed_jobs: Set[str] = set()
            job_levels = dag.can_run_parallel()
            
            for level in job_levels:
                if failed_jobs:
                    break  # Fail fast
                
                # Run jobs in this level concurrently
                tasks = []
                for job_name in level:
                    if job_name not in completed_jobs:
                        task = self._execute_job(
                            job_name,
                            workflow['jobs'][job_name],
                            workflow['env'],
                            run_metadata
                        )
                        tasks.append((job_name, task))
                
                # Wait for all jobs in this level to complete
                for job_name, task in tasks:
                    try:
                        await task
                        completed_jobs.add(job_name)
                        self._log(f"✅ Job '{job_name}' completed")
                    except Exception as e:
                        failed_jobs.add(job_name)
                        self._log(f"❌ Job '{job_name}' failed: {e}")
                        run_metadata['jobs'][job_name]['error'] = str(e)
            
            # Update final status
            end_time = time.time()
            run_metadata.update({
                'end_time': end_time,
                'duration': end_time - start_time,
                'status': 'failed' if failed_jobs else 'success',
                'completed_jobs': list(completed_jobs),
                'failed_jobs': list(failed_jobs)
            })
            
            # Save run history
            await self._save_run_metadata(run_metadata)
            
            if failed_jobs:
                raise WorkflowExecutionError(f"Workflow failed. Failed jobs: {failed_jobs}")
            
            self._log(f"🎉 Workflow completed successfully in {run_metadata['duration']:.1f}s")
            return run_metadata
            
        except Exception as e:
            # Save failed run metadata
            run_metadata.update({
                'end_time': time.time(),
                'status': 'error',
                'error': str(e)
            })
            await self._save_run_metadata(run_metadata)
            raise
    
    async def _execute_job(self, job_name: str, job_config: Dict[str, Any],
                          global_env: Dict[str, Any], run_metadata: Dict[str, Any]):
        """Execute a single job with its steps"""
        job_start = time.time()
        
        run_metadata['jobs'][job_name] = {
            'start_time': job_start,
            'status': 'running',
            'steps': []
        }
        
        self._log(f"🔄 Starting job: {job_name}")
        
        # Merge environment variables and variables
        env = {**global_env, **job_config.get('env', {})}
        job_vars: Dict[str, Any] = {**self.global_vars, **job_config.get('vars', {})}
        
        try:
            # Execute steps sequentially
            for i, step in enumerate(job_config.get('steps', [])):
                step_start = time.time()
                step_metadata = {
                    'index': i,
                    'uses': step['uses'],
                    'start_time': step_start,
                    'status': 'running'
                }
                run_metadata['jobs'][job_name]['steps'].append(step_metadata)
                
                await self._execute_step(step, env, job_vars, job_name, i)
                
                step_metadata.update({
                    'end_time': time.time(),
                    'status': 'success'
                })
            
            run_metadata['jobs'][job_name].update({
                'end_time': time.time(),
                'status': 'success'
            })
            
        except Exception as e:
            run_metadata['jobs'][job_name].update({
                'end_time': time.time(),
                'status': 'failed',
                'error': str(e)
            })
            raise
    
    async def _execute_step(
        self,
        step: Dict[str, Any],
        env: Dict[str, Any],
        vars_map: Dict[str, Any],
        job_name: str,
        step_index: int,
    ):
        """Execute a single step"""
        plugin_path = step['uses']
        # Start from step's with-config, then apply CLI-provided overrides for this plugin
        step_with = dict(step.get('with', {}))
        if plugin_path in self.step_overrides:
            step_with.update(self.step_overrides[plugin_path])
        
        self._log(f"  📦 [{job_name}] Step {step_index}: {plugin_path}")
        
        # Interpolate variables into `with` values
        interpolated_with = self._interpolate(step_with, env=env, vars_map=vars_map)

        # Create step context
        ctx = {
            'env': env,
            'step': step,
            'workspace': self.workspace,
            'logger': self._log,
            'with': interpolated_with
        }
        
        try:
            await load_plugin(plugin_path, ctx)
        except Exception as e:
            raise WorkflowExecutionError(f"Step {step_index} failed: {e}")

    def _interpolate(self, data: Any, env: Dict[str, Any], vars_map: Dict[str, Any]) -> Any:
        """Recursively interpolate strings in data using vars and env.

        Supports:
          - Python format-like: "{myvar}"
          - GitHub Actions-like: "${{ vars.myvar }}" and "${{ env.MY_ENV }}"
        """
        import re

        def replace_in_string(s: str) -> str:
            # 1) Handle ${{ ... }} expressions
            def gh_replace(match: re.Match[str]) -> str:
                expr = match.group(1).strip()
                # support vars.foo and env.BAR
                if expr.startswith('vars.'):
                    key = expr[len('vars.'):]
                    return str(vars_map.get(key, ''))
                if expr.startswith('env.'):
                    key = expr[len('env.'):]
                    return str(env.get(key, ''))
                # fallback to env then vars
                return str(env.get(expr, vars_map.get(expr, '')))

            s2 = re.sub(r"\$\{\{\s*([^}]+?)\s*\}\}", gh_replace, s)

            # 2) Handle {var} braces, but avoid KeyError if missing
            class SafeDict(dict):
                def __missing__(self, key):  # type: ignore[override]
                    return ""

            combined = SafeDict({**{str(k): str(v) for k, v in vars_map.items()},
                                 **{str(k): str(v) for k, v in env.items()}})
            try:
                return s2.format_map(combined)
            except Exception:
                return s2

        if isinstance(data, str):
            return replace_in_string(data)
        if isinstance(data, list):
            return [self._interpolate(v, env, vars_map) for v in data]
        if isinstance(data, dict):
            return {k: self._interpolate(v, env, vars_map) for k, v in data.items()}
        return data
    
    async def _save_run_metadata(self, metadata: Dict[str, Any]):
        """Save run metadata to history"""
        filename = f"{metadata['run_id']}.json"
        filepath = self.history_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
    
    def _log(self, message: str):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")


async def run_workflow(
    workflow_path: Path,
    workspace: Optional[Path] = None,
    step_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
    vars_overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Convenience function to run a workflow"""
    engine = WorkflowEngine(workspace, step_overrides, vars_overrides)
    return await engine.run(workflow_path)
