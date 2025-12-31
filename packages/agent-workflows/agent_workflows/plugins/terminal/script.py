"""Run a script file with optional interpreter

with:
  path: <str>                 # required - script path relative to workspace
  args: <list[str]>           # optional - args to pass to the script
  interpreter: <str>          # optional - interpreter executable (e.g., python, bash)
  env: <dict[str,str]>        # optional - extra env vars
  timeout: <int>              # optional - seconds before killing (0 = none)
  continue_on_error: <bool>   # optional - don't fail step on nonzero exit
  make_executable: <bool>     # optional - chmod +x before run (default: true)
  cwd: <str>                  # optional - working directory override
"""

from __future__ import annotations

import asyncio
import os
import stat
from asyncio.subprocess import PIPE
from pathlib import Path
from typing import Any, Dict, List, Optional


async def _run(
    argv: List[str], cwd: Path, env: Dict[str, str], timeout_seconds: Optional[int], logger
) -> int:
    logger(f"  💻 {' '.join(argv)}")
    process = await asyncio.create_subprocess_exec(
        *argv,
        cwd=str(cwd),
        stdout=PIPE,
        stderr=PIPE,
        env=env,
    )
    try:
        if timeout_seconds and timeout_seconds > 0:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout_seconds)
        else:
            stdout, stderr = await process.communicate()
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        logger("    ⏱️ Timeout - process killed")
        return 124

    if stdout:
        logger(f"    📤 {stdout.decode().rstrip()}")
    if process.returncode != 0:
        err = stderr.decode().rstrip()
        if err:
            logger(f"    ❌ {err}")
    return int(process.returncode if process.returncode is not None else 0)


async def execute(ctx: Dict[str, Any]) -> None:
    logger = ctx["logger"]
    workspace: Path = ctx["workspace"]
    step_with: Dict[str, Any] = ctx.get("with", {})

    path_str = step_with.get("path")
    if not isinstance(path_str, str) or not path_str:
        raise ValueError("'with.path' is required and must be a string")

    cwd_override = step_with.get("cwd")
    if isinstance(cwd_override, str) and cwd_override:
        base_dir = (workspace / cwd_override).resolve()
    else:
        base_dir = workspace

    script_path = (base_dir / path_str).resolve()
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    args = step_with.get("args") or []
    if not isinstance(args, list):
        raise ValueError("'with.args' must be a list of strings if provided")

    interpreter = step_with.get("interpreter")
    extra_env = step_with.get("env") or {}
    if not isinstance(extra_env, dict):
        raise ValueError("'with.env' must be a mapping of str->str if provided")

    base_env = os.environ.copy()
    ctx_env = ctx.get("env", {}) or {}
    for k, v in ctx_env.items():
        base_env[str(k)] = str(v)
    for k, v in extra_env.items():
        base_env[str(k)] = str(v)

    timeout_val = step_with.get("timeout", 0)
    try:
        timeout_seconds: Optional[int] = int(timeout_val)
    except Exception:
        raise ValueError("'with.timeout' must be an integer number of seconds")
    continue_on_error: bool = bool(step_with.get("continue_on_error", False))
    make_executable: bool = step_with.get("make_executable", True)

    if make_executable:
        try:
            current_mode = script_path.stat().st_mode
            script_path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        except Exception:
            # Don't hard-fail on chmod issues; the run may still work with interpreter
            pass

    if interpreter:
        argv: List[str] = [str(interpreter), str(script_path), *[str(a) for a in args]]
    else:
        argv = [str(script_path), *[str(a) for a in args]]

    logger("🧨 Running script")
    if isinstance(cwd_override, str) and cwd_override:
        working_dir = base_dir
    else:
        working_dir = script_path.parent
    exit_code = await _run(
        argv, cwd=working_dir, env=base_env, timeout_seconds=timeout_seconds, logger=logger
    )
    if exit_code != 0 and not continue_on_error:
        raise RuntimeError(f"Script failed with exit code {exit_code}")
    logger("✅ Script finished")


