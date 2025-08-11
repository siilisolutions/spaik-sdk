"""Git download plugin

Downloads files from a Git repository into the current workspace.

with:
  repo: <str>                  # required - repository URL (HTTPS/SSH)
  ref: <str>                   # optional - branch/tag/commit (default: repository default)
  files: <list[str]>           # optional - list of file paths or glob patterns to copy
  dest: <str>                  # optional - destination subdirectory in workspace (default: ".")
  depth: <int>                 # optional - shallow clone depth (default: 1)

Behavior:
- If files are provided, only those files (or glob matches) are copied from the repo checkout.
  - For files, only the filename is placed under `dest` (the repo's directory path is not preserved).
  - For directories, the directory's CONTENTS are copied under `dest` (the top-level directory name is not included), while preserving the sub-structure inside that directory.
- If files are omitted, the entire repository contents (excluding .git) are copied into dest.
"""

from __future__ import annotations

import asyncio
from asyncio.subprocess import PIPE
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class DownloadConfig:
    repo: str
    ref: Optional[str]
    files: Optional[List[str]]
    dest: Path
    depth: int


async def _run_command(cmd: List[str], cwd: Optional[Path], logger) -> None:
    cmd_display = " ".join(cmd)
    logger(f"  💻 {cmd_display}")
    process = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(cwd) if cwd else None,
        stdout=PIPE,
        stderr=PIPE,
    )
    stdout, stderr = await process.communicate()
    if stdout:
        logger(f"    📤 {stdout.decode().strip()}")
    if process.returncode != 0:
        err = stderr.decode().strip()
        raise RuntimeError(f"Command failed ({process.returncode}): {cmd_display}\n{err}")


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _copy_tree(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name == ".git":
            continue
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            _ensure_parent_dir(target)
            shutil.copy2(item, target)


def _glob_many(base: Path, patterns: Iterable[str]) -> List[Path]:
    matched: List[Path] = []
    for pattern in patterns:
        # If pattern is an exact path, include it even if glob finds nothing
        exact = base / pattern
        hits = list(base.glob(pattern))
        if hits:
            matched.extend(hits)
        elif exact.exists():
            matched.append(exact)
    # Deduplicate while preserving order
    seen = set()
    unique: List[Path] = []
    for p in matched:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            unique.append(p)
    return unique


def _copy_selected_files(repo_dir: Path, dest_dir: Path, files: List[Path]) -> List[str]:
    copied: List[str] = []
    for src in files:
        # Compute paths relative to repo
        rel = src.relative_to(repo_dir)

        if src.is_dir():
            # When a directory is selected, drop the top-level directory name
            # and place its contents directly under dest, preserving internal structure
            for item in src.rglob("*"):
                if ".git" in item.parts:
                    continue
                if item.is_dir():
                    # Ensure directories exist to preserve internal structure
                    relative_in_dir = item.relative_to(src)
                    target_dir = dest_dir / relative_in_dir
                    target_dir.mkdir(parents=True, exist_ok=True)
                    continue
                # Files
                relative_in_dir = item.relative_to(src)
                dst_file = dest_dir / relative_in_dir
                _ensure_parent_dir(dst_file)
                shutil.copy2(item, dst_file)
            copied.append(str(rel) + "/ (flattened)")
        elif src.is_file():
            # Flatten file destination: drop repo subdirectories, keep only basename
            dst_file = dest_dir / src.name
            _ensure_parent_dir(dst_file)
            shutil.copy2(src, dst_file)
            copied.append(src.name)
    return copied


async def execute(ctx: Dict[str, Any]) -> None:
    logger = ctx["logger"]
    workspace: Path = ctx["workspace"]
    step_with: Dict[str, Any] = ctx.get("with", {})

    repo = step_with.get("repo")
    if not repo or not isinstance(repo, str):
        raise ValueError("'with.repo' is required and must be a string")

    ref = step_with.get("ref")
    files = step_with.get("files")
    if files is not None and not isinstance(files, list):
        raise ValueError("'with.files' must be a list of strings if provided")
    dest_str = step_with.get("dest", ".")
    depth = int(step_with.get("depth", 1))

    config = DownloadConfig(
        repo=repo,
        ref=ref if isinstance(ref, str) and ref.strip() else None,
        files=[str(f) for f in files] if isinstance(files, list) else None,
        dest=(workspace / dest_str).resolve(),
        depth=depth if depth > 0 else 1,
    )

    logger(f"📥 Downloading from {config.repo}" + (f"@{config.ref}" if config.ref else ""))
    if config.files:
        logger(f"  🎯 Selecting {len(config.files)} path(s)")
    logger(f"  📂 Destination: {config.dest}")

    # Prepare temp directory inside workspace to keep things contained
    tmp_root = workspace / ".agent-workflows" / "tmp"
    tmp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=tmp_root) as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)

        # Shallow clone
        clone_cmd: List[str] = [
            "git",
            "clone",
            "--depth",
            str(config.depth),
            "--single-branch",
        ]
        if config.ref:
            clone_cmd.extend(["--branch", config.ref])
        clone_cmd.extend([config.repo, str(tmp_dir)])
        await _run_command(clone_cmd, cwd=None, logger=logger)

        # Ensure destination exists
        config.dest.mkdir(parents=True, exist_ok=True)

        if config.files:
            matches = _glob_many(tmp_dir, config.files)
            if not matches:
                raise FileNotFoundError(
                    f"No files matched given patterns: {config.files}"
                )
            copied = _copy_selected_files(tmp_dir, config.dest, matches)
            logger(f"✅ Copied {len(copied)} item(s):")
            for name in copied:
                logger(f"   - {name}")
        else:
            _copy_tree(tmp_dir, config.dest)
            logger("✅ Copied repository contents")

    logger("🎉 Git download completed")


