"""DAG utilities for workflow execution"""

from typing import Dict, List, Set
from collections import defaultdict, deque


class CyclicDependencyError(Exception):
    """Raised when circular dependencies are detected"""
    pass


class DAG:
    """Directed Acyclic Graph for job dependencies"""
    
    def __init__(self, dependencies: Dict[str, List[str]]):
        self.nodes = set(dependencies.keys())
        self.dependencies = dependencies
        self._validate_dependencies()
        self._detect_cycles()
    
    def _validate_dependencies(self):
        """Ensure all dependencies reference valid nodes"""
        for node, deps in self.dependencies.items():
            for dep in deps:
                if dep not in self.nodes:
                    raise ValueError(f"Node '{node}' depends on unknown node '{dep}'")
    
    def _detect_cycles(self):
        """Detect circular dependencies using DFS"""
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str) -> bool:
            if node in rec_stack:
                return True
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for dep in self.dependencies.get(node, []):
                if has_cycle(dep):
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in self.nodes:
            if node not in visited and has_cycle(node):
                raise CyclicDependencyError(f"Circular dependency detected involving '{node}'")
    
    def topological_sort(self) -> List[str]:
        """Return nodes in topologically sorted order using Kahn's algorithm"""
        # Calculate in-degrees
        in_degree = defaultdict(int)
        for node in self.nodes:
            in_degree[node] = 0
        
        for node, deps in self.dependencies.items():
            for dep in deps:
                in_degree[node] += 1
        
        # Start with nodes that have no dependencies
        queue = deque([node for node in self.nodes if in_degree[node] == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            # Remove this node and update in-degrees
            for other_node, deps in self.dependencies.items():
                if node in deps:
                    in_degree[other_node] -= 1
                    if in_degree[other_node] == 0:
                        queue.append(other_node)
        
        if len(result) != len(self.nodes):
            raise CyclicDependencyError("Unable to sort - circular dependencies exist")
        
        return result
    
    def get_ready_jobs(self, completed: Set[str]) -> List[str]:
        """Get jobs that can run now (all dependencies completed)"""
        ready = []
        for node in self.nodes:
            if node not in completed:
                deps = set(self.dependencies.get(node, []))
                if deps.issubset(completed):
                    ready.append(node)
        return ready
    
    def can_run_parallel(self) -> List[List[str]]:
        """Group jobs that can run in parallel"""
        sorted_jobs = self.topological_sort()
        completed: Set[str] = set()
        levels = []
        
        while len(completed) < len(self.nodes):
            current_level = []
            for job in sorted_jobs:
                if job not in completed:
                    deps = set(self.dependencies.get(job, []))
                    if deps.issubset(completed):
                        current_level.append(job)
            
            if not current_level:
                break
                
            levels.append(current_level)
            completed.update(current_level)
        
        return levels