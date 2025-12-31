"""Run arbitrary terminal commands

with:
  cmd: <str|list[str]>        # required - command to run (string or argv list)
  cwd: <str>                  # optional - working directory relative to workspace
  env: <dict[str,str]>        # optional - extra env vars
  timeout: <int>              # optional - seconds before killing (0 = no timeout)
  shell: <bool>               # optional - run via shell for string commands (default: false)
  continue_on_error: <bool>   # optional - don't fail step on nonzero exit (default: false)
"""

from __future__ import annotations

import asyncio
import os
from asyncio.subprocess import PIPE
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


async def _run_subprocess(
    argv_or_str: Union[str, List[str]],
    cwd: Optional[Path],
    env: Dict[str, str],
    use_shell: bool,
    logger,
    timeout_seconds: Optional[int],
) -> int:
    display = " ".join(argv_or_str) if isinstance(argv_or_str, list) else argv_or_str
    logger(f"  💻 {display}")

    if use_shell:
        cmd_str: str
        if isinstance(argv_or_str, list):
            cmd_str = " ".join(argv_or_str)
        else:
            assert isinstance(argv_or_str, str)  # for type checker
            cmd_str = argv_or_str
        process = await asyncio.create_subprocess_shell(
            cmd_str,
            cwd=str(cwd) if cwd else None,
            stdout=PIPE,
            stderr=PIPE,
            env=env,
        )
    else:
        if isinstance(argv_or_str, str):
            args_list: List[str] = argv_or_str.split()
        else:
            args_list = argv_or_str
        process = await asyncio.create_subprocess_exec(
            *args_list,
            cwd=str(cwd) if cwd else None,
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
        return 124  # common timeout code

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

    cmd: Union[str, List[str], None] = step_with.get("cmd")
    if cmd is None:
        raise ValueError("'with.cmd' is required")

    cwd_str = step_with.get("cwd")
    cwd = (workspace / cwd_str).resolve() if isinstance(cwd_str, str) and cwd_str else None

    extra_env = step_with.get("env") or {}
    if not isinstance(extra_env, dict):
        raise ValueError("'with.env' must be a mapping of str->str if provided")

    # Merge base env from ctx with provided env
    base_env = os.environ.copy()
    # ctx env may contain workflow-level variables; stringify
    ctx_env = ctx.get("env", {}) or {}
    for k, v in ctx_env.items():
        base_env[str(k)] = str(v)
    for k, v in extra_env.items():
        base_env[str(k)] = str(v)

    shell: bool = bool(step_with.get("shell", False))
    timeout_val = step_with.get("timeout", 0)
    try:
        timeout_seconds: Optional[int] = int(timeout_val)
    except Exception:
        raise ValueError("'with.timeout' must be an integer number of seconds")
    continue_on_error: bool = bool(step_with.get("continue_on_error", False))

    logger("🧨 Running command")
    exit_code = await _run_subprocess(
        cmd, cwd=cwd, env=base_env, use_shell=shell, logger=logger,
        timeout_seconds=timeout_seconds,
    )
    if exit_code != 0 and not continue_on_error:
        raise RuntimeError(f"Command failed with exit code {exit_code}")
    logger("✅ Command finished")


