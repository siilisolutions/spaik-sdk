"""Tests for workflow parser"""

import pytest
import tempfile
from pathlib import Path

from agent_workflows.parser import load_workflow, validate_workflow, WorkflowParseError


def test_load_valid_workflow():
    """Test loading a valid workflow file"""
    yaml_content = """
name: test-workflow
env:
  NODE_ENV: test
jobs:
  build:
    steps:
      - uses: npm/install@v1
      - uses: npm/build@v1
  test:
    needs: build
    steps:
      - uses: npm/test@v1
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write(yaml_content)
        f.flush()
        
        workflow = load_workflow(Path(f.name))
        
        assert workflow['name'] == 'test-workflow'
        assert workflow['env']['NODE_ENV'] == 'test'
        assert len(workflow['jobs']) == 2
        assert 'build' in workflow['jobs']
        assert 'test' in workflow['jobs']
        assert workflow['jobs']['test']['needs'] == ['build']


def test_load_nonexistent_file():
    """Test loading a file that doesn't exist"""
    with pytest.raises(WorkflowParseError, match="Workflow file not found"):
        load_workflow(Path("/nonexistent/file.yml"))


def test_invalid_yaml():
    """Test loading invalid YAML"""
    yaml_content = """
name: test
jobs:
  build:
    steps:
      - uses: something
      invalid_yaml: [unclosed
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write(yaml_content)
        f.flush()
        
        with pytest.raises(WorkflowParseError, match="Invalid YAML"):
            load_workflow(Path(f.name))


def test_validate_workflow_missing_jobs():
    """Test validation fails when jobs are missing"""
    data = {"name": "test"}
    
    with pytest.raises(WorkflowParseError, match="Workflow must have 'jobs' field"):
        validate_workflow(data)


def test_validate_workflow_invalid_job_needs():
    """Test validation fails when job references unknown dependency"""
    data = {
        "name": "test",
        "jobs": {
            "test": {
                "needs": ["nonexistent"],
                "steps": [{"uses": "test@v1"}]
            }
        }
    }
    
    with pytest.raises(WorkflowParseError, match="depends on unknown job"):
        validate_workflow(data)


def test_validate_workflow_missing_step_uses():
    """Test validation fails when step is missing uses"""
    data = {
        "name": "test",
        "jobs": {
            "test": {
                "steps": [{"with": {"foo": "bar"}}]
            }
        }
    }
    
    with pytest.raises(WorkflowParseError, match="must have 'uses' field"):
        validate_workflow(data)


def test_validate_workflow_sets_defaults():
    """Test that validation sets appropriate defaults"""
    data = {
        "jobs": {
            "test": {
                "steps": [{"uses": "test@v1"}]
            }
        }
    }
    
    result = validate_workflow(data)
    
    assert result['name'] == 'unnamed-workflow'
    assert result['env'] == {}
    assert 'jobs' in result


def test_validate_job_needs_string_or_list():
    """Test that job needs can be string or list"""
    # String needs
    data1 = {
        "jobs": {
            "job1": {"steps": [{"uses": "test@v1"}]},
            "job2": {"needs": "job1", "steps": [{"uses": "test@v1"}]}
        }
    }
    result1 = validate_workflow(data1)
    assert result1['jobs']['job2']['needs'] == ['job1']
    
    # List needs
    data2 = {
        "jobs": {
            "job1": {"steps": [{"uses": "test@v1"}]},
            "job2": {"steps": [{"uses": "test@v1"}]},
            "job3": {"needs": ["job1", "job2"], "steps": [{"uses": "test@v1"}]}
        }
    }
    result2 = validate_workflow(data2)
    assert result2['jobs']['job3']['needs'] == ["job1", "job2"]