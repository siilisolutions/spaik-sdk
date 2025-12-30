"""Git changes detection and serialization."""

import json
import subprocess
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional


class ChangeType(str, Enum):
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"
    COPIED = "copied"
    UNTRACKED = "untracked"


@dataclass
class FileChange:
    """Represents a change to a single file."""
    path: str
    change_type: ChangeType
    diff: Optional[str] = None
    old_path: Optional[str] = None  # For renames
    staged: bool = False
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d["change_type"] = self.change_type.value
        return d


@dataclass
class GitChanges:
    """All changes in a git repository."""
    staged: List[FileChange]
    unstaged: List[FileChange]
    untracked: List[FileChange]
    branch: str
    commit: Optional[str] = None  # Current HEAD commit
    
    def to_dict(self) -> dict:
        return {
            "branch": self.branch,
            "commit": self.commit,
            "staged": [f.to_dict() for f in self.staged],
            "unstaged": [f.to_dict() for f in self.unstaged],
            "untracked": [f.to_dict() for f in self.untracked],
        }
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)
    
    @property
    def has_changes(self) -> bool:
        return bool(self.staged or self.unstaged or self.untracked)
    
    @property
    def total_files(self) -> int:
        return len(self.staged) + len(self.unstaged) + len(self.untracked)


def _run_git(args: List[str], cwd: Optional[Path] = None) -> str:
    """Run a git command and return output."""
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout


def _get_repo_root(cwd: Optional[Path] = None) -> Path:
    """Get the root directory of the git repository."""
    root = _run_git(["rev-parse", "--show-toplevel"], cwd).strip()
    return Path(root)


def _parse_status_code(code: str) -> ChangeType:
    """Parse git status code to ChangeType."""
    if code == "A":
        return ChangeType.ADDED
    elif code == "M":
        return ChangeType.MODIFIED
    elif code == "D":
        return ChangeType.DELETED
    elif code == "R":
        return ChangeType.RENAMED
    elif code == "C":
        return ChangeType.COPIED
    elif code == "?":
        return ChangeType.UNTRACKED
    else:
        return ChangeType.MODIFIED  # Default


def _get_diff(path: str, staged: bool, cwd: Optional[Path] = None) -> Optional[str]:
    """Get diff for a file."""
    try:
        args = ["diff"]
        if staged:
            args.append("--cached")
        args.append("--")
        args.append(path)
        return _run_git(args, cwd).strip() or None
    except RuntimeError:
        return None


def get_changes(repo_path: Optional[Path] = None, include_diffs: bool = True) -> GitChanges:
    """Get all changes in a git repository.
    
    Args:
        repo_path: Path to the git repository. Defaults to current directory.
        include_diffs: Whether to include file diffs. Defaults to True.
    
    Returns:
        GitChanges object with all staged, unstaged, and untracked changes.
    """
    cwd = repo_path or Path.cwd()
    # Always use repo root for consistent paths
    cwd = _get_repo_root(cwd)
    
    # Get current branch
    try:
        branch = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd).strip()
    except RuntimeError:
        branch = "unknown"
    
    # Get current commit
    try:
        commit = _run_git(["rev-parse", "HEAD"], cwd).strip()
    except RuntimeError:
        commit = None
    
    # Get status with porcelain format for parsing
    status_output = _run_git(["status", "--porcelain=v1", "-z"], cwd)
    
    staged: List[FileChange] = []
    unstaged: List[FileChange] = []
    untracked: List[FileChange] = []
    
    # Parse porcelain output (null-separated)
    entries = status_output.split("\0")
    i = 0
    while i < len(entries):
        entry = entries[i]
        if not entry:
            i += 1
            continue
        
        # Format: XY filename
        # X = staged status, Y = unstaged status
        if len(entry) < 3:
            i += 1
            continue
            
        staged_code = entry[0]
        unstaged_code = entry[1]
        path = entry[3:]
        
        # Handle renames (have an extra entry for old path)
        old_path = None
        if staged_code == "R" or unstaged_code == "R":
            i += 1
            if i < len(entries):
                old_path = entries[i]
        
        # Staged changes
        if staged_code not in (" ", "?"):
            diff = _get_diff(path, staged=True, cwd=cwd) if include_diffs else None
            staged.append(FileChange(
                path=path,
                change_type=_parse_status_code(staged_code),
                diff=diff,
                old_path=old_path,
                staged=True,
            ))
        
        # Unstaged changes
        if unstaged_code not in (" ", "?"):
            diff = _get_diff(path, staged=False, cwd=cwd) if include_diffs else None
            unstaged.append(FileChange(
                path=path,
                change_type=_parse_status_code(unstaged_code),
                diff=diff,
                old_path=old_path,
                staged=False,
            ))
        
        # Untracked files
        if staged_code == "?" and unstaged_code == "?":
            untracked.append(FileChange(
                path=path,
                change_type=ChangeType.UNTRACKED,
                diff=None,
                staged=False,
            ))
        
        i += 1
    
    return GitChanges(
        staged=staged,
        unstaged=unstaged,
        untracked=untracked,
        branch=branch,
        commit=commit,
    )


def main() -> None:
    """Print git changes as JSON."""
    import sys
    
    repo_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    
    try:
        changes = get_changes(repo_path)
        print(changes.to_json())
    except RuntimeError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

