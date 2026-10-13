"""Check aligned public versions before publishing; emits npm_tag to Actions."""

import json
import os
import re
import tomllib
from pathlib import Path

version = os.environ["RELEASE_VERSION"]
if not re.fullmatch(r"1\.0\.\d+(?:rc\d+)?|1\.[1-9]\d*\.\d+", version):
    raise SystemExit("Use a stable 1.x version or a 1.0.xrcN candidate")
npm_version = re.sub(r"rc(\d+)$", r"-rc.\1", version)
python = tomllib.loads(Path("packages/agent-sdk/pyproject.toml").read_text())[
    "project"
]["version"]
if python != version:
    raise SystemExit("Commit the requested SDK version before publishing")
for path in [
    "packages/agent-sdk-hooks/package.json",
    "packages/agent-sdk-material/package.json",
]:
    if json.loads(Path(path).read_text())["version"] != npm_version:
        raise SystemExit(f"Unaligned npm version in {path}")
tag = "next" if "rc" in version else "latest"
if os.environ.get("GITHUB_OUTPUT"):
    with open(os.environ["GITHUB_OUTPUT"], "a") as file:
        file.write(f"npm_tag={tag}\nnpm_version={npm_version}\n")
print(f"Validated Python {version}, npm {npm_version}, npm tag {tag}")
