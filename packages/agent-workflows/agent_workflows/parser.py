"""YAML workflow parser"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional


class WorkflowParseError(Exception):
    """Raised when workflow YAML is invalid"""
    pass


def load_workflow(path: Path) -> Dict[str, Any]:
    """Load and validate a .uvx.yml workflow file"""
    if not path.exists():
        raise WorkflowParseError(f"Workflow file not found: {path}")
    
    try:
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise WorkflowParseError(f"Invalid YAML: {e}")
    
    return validate_workflow(data)


def validate_workflow(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate workflow structure"""
    if not isinstance(data, dict):
        raise WorkflowParseError("Workflow must be a dictionary")
    
    # Required fields
    if 'jobs' not in data:
        raise WorkflowParseError("Workflow must have 'jobs' field")
    
    # Validate jobs
    jobs = data.get('jobs', {})
    if not isinstance(jobs, dict):
        raise WorkflowParseError("'jobs' must be a dictionary")
    
    for job_name, job_config in jobs.items():
        validate_job(job_name, job_config, jobs)
    
    # Set defaults
    return {
        'name': data.get('name', 'unnamed-workflow'),
        'env': data.get('env', {}),
        # Optional variables block for template interpolation
        'vars': data.get('vars', {}),
        'jobs': jobs
    }


def validate_job(job_name: str, job_config: Dict[str, Any], all_jobs: Dict[str, Any]):
    """Validate a single job configuration"""
    if not isinstance(job_config, dict):
        raise WorkflowParseError(f"Job '{job_name}' must be a dictionary")
    
    # Validate steps
    steps = job_config.get('steps', [])
    if not isinstance(steps, list):
        raise WorkflowParseError(f"Job '{job_name}' steps must be a list")
    
    for i, step in enumerate(steps):
        validate_step(job_name, i, step)
    
    # Validate needs dependencies
    needs = job_config.get('needs', [])
    if isinstance(needs, str):
        needs = [needs]
    elif not isinstance(needs, list):
        raise WorkflowParseError(f"Job '{job_name}' needs must be string or list")
    
    for dep in needs:
        if dep not in all_jobs:
            raise WorkflowParseError(f"Job '{job_name}' depends on unknown job '{dep}'")
    
    # Normalize needs to always be a list
    job_config['needs'] = needs


def validate_step(job_name: str, step_index: int, step: Dict[str, Any]):
    """Validate a single step configuration"""
    if not isinstance(step, dict):
        raise WorkflowParseError(f"Job '{job_name}' step {step_index} must be a dictionary")
    
    if 'uses' not in step:
        raise WorkflowParseError(f"Job '{job_name}' step {step_index} must have 'uses' field")
    
    uses = step['uses']
    if not isinstance(uses, str):
        raise WorkflowParseError(f"Job '{job_name}' step {step_index} 'uses' must be a string")


def get_job_dependencies(jobs: Dict[str, Any]) -> Dict[str, List[str]]:
    """Extract dependency graph from jobs"""
    deps = {}
    for job_name, job_config in jobs.items():
        needs = job_config.get('needs', [])
        if isinstance(needs, str):
            needs = [needs]
        deps[job_name] = needs
    return deps