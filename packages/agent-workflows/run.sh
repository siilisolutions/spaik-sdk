#!/usr/bin/env bash

# Usage:
#   ./run.sh apply-template --template agent --path testicle

workflow_prefix="$1"
shift || true

uv run -m agent_workflows.cli run -f "${workflow_prefix}.agent-workflow.yml" "$@"


