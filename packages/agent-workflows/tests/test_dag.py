"""Tests for DAG utilities"""

import pytest
from agent_workflows.dag import DAG, CyclicDependencyError


def test_dag_simple_dependencies():
    """Test DAG with simple linear dependencies"""
    deps = {
        'job1': [],
        'job2': ['job1'],
        'job3': ['job2']
    }
    
    dag = DAG(deps)
    sorted_jobs = dag.topological_sort()
    
    assert sorted_jobs == ['job1', 'job2', 'job3']


def test_dag_parallel_jobs():
    """Test DAG with parallel jobs"""
    deps = {
        'job1': [],
        'job2': [],
        'job3': ['job1'],
        'job4': ['job2'],
        'job5': ['job3', 'job4']
    }
    
    dag = DAG(deps)
    sorted_jobs = dag.topological_sort()
    
    # job1 and job2 can be in any order, but must come first
    assert sorted_jobs[0] in ['job1', 'job2']
    assert sorted_jobs[1] in ['job1', 'job2']
    assert sorted_jobs[0] != sorted_jobs[1]
    
    # job5 must be last
    assert sorted_jobs[-1] == 'job5'


def test_dag_detect_cycle():
    """Test cycle detection"""
    deps = {
        'job1': ['job2'],
        'job2': ['job3'],
        'job3': ['job1']  # Creates cycle
    }
    
    with pytest.raises(CyclicDependencyError):
        DAG(deps)


def test_dag_self_cycle():
    """Test self-referencing cycle detection"""
    deps = {
        'job1': ['job1']  # Self cycle
    }
    
    with pytest.raises(CyclicDependencyError):
        DAG(deps)


def test_dag_unknown_dependency():
    """Test validation of unknown dependencies"""
    deps = {
        'job1': ['nonexistent']
    }
    
    with pytest.raises(ValueError, match="depends on unknown node"):
        DAG(deps)


def test_dag_get_ready_jobs():
    """Test getting jobs that are ready to run"""
    deps = {
        'job1': [],
        'job2': [],
        'job3': ['job1'],
        'job4': ['job1', 'job2']
    }
    
    dag = DAG(deps)
    
    # Initially, only job1 and job2 can run
    ready = dag.get_ready_jobs(set())
    assert set(ready) == {'job1', 'job2'}
    
    # After job1 completes, job3 becomes ready
    ready = dag.get_ready_jobs({'job1'})
    assert set(ready) == {'job2', 'job3'}
    
    # After both job1 and job2 complete, job4 becomes ready
    ready = dag.get_ready_jobs({'job1', 'job2'})
    assert set(ready) == {'job3', 'job4'}


def test_dag_parallel_levels():
    """Test grouping jobs into parallel execution levels"""
    deps = {
        'job1': [],
        'job2': [],
        'job3': ['job1'],
        'job4': ['job2'],
        'job5': ['job3', 'job4']
    }
    
    dag = DAG(deps)
    levels = dag.can_run_parallel()
    
    assert len(levels) == 3
    assert set(levels[0]) == {'job1', 'job2'}  # Can run in parallel
    assert set(levels[1]) == {'job3', 'job4'}  # Can run in parallel after level 0
    assert levels[2] == ['job5']  # Must wait for level 1


def test_dag_no_dependencies():
    """Test DAG with no dependencies (all parallel)"""
    deps = {
        'job1': [],
        'job2': [],
        'job3': []
    }
    
    dag = DAG(deps)
    levels = dag.can_run_parallel()
    
    assert len(levels) == 1
    assert set(levels[0]) == {'job1', 'job2', 'job3'}


def test_dag_complex_dependencies():
    """Test DAG with complex dependency graph"""
    deps = {
        'build': [],
        'lint': [],
        'test': ['build'],
        'integration': ['build'],
        'security': ['build'],
        'deploy': ['test', 'integration', 'security'],
        'notify': ['deploy']
    }
    
    dag = DAG(deps)
    levels = dag.can_run_parallel()
    
    # First level: build and lint (no dependencies)
    assert set(levels[0]) == {'build', 'lint'}
    
    # Second level: test, integration, security (depend on build)
    assert set(levels[1]) == {'test', 'integration', 'security'}
    
    # Third level: deploy (depends on test, integration, security)
    assert levels[2] == ['deploy']
    
    # Fourth level: notify (depends on deploy)
    assert levels[3] == ['notify']