#!/usr/bin/env bash

set -euo pipefail

# Generate Cursor .mdc rule files from docs and install them into template directories.

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

docs_dir="$repo_root/docs/ai-instructions"

backend_src="$docs_dir/AI_BACKEND_INSTRUCTIONS.md"
frontend_src="$docs_dir/AI_FRONTEND_INSTRUCTIONS.md"
server_src="$docs_dir/AI_SERVER_INSTRUCTIONS.md"

require_file() {
  local file_path="$1"
  if [[ ! -f "$file_path" ]]; then
    echo "ERROR: Missing source file: $file_path" >&2
    exit 1
  fi
}

require_file "$backend_src"
require_file "$frontend_src"
require_file "$server_src"

write_rule() {
  local dest_file="$1"
  local description="$2"
  local src_file="$3"

  mkdir -p "$(dirname "$dest_file")"

  {
    printf -- '---\n'
    printf 'description: %s\n' "$description"
    printf 'globs: \n'
    printf 'alwaysApply: false\n'
    printf -- '---\n\n'
    cat "$src_file"
  } > "$dest_file"
}

install_rule_to_template() {
  local template_dir="$1"       # e.g. /.../templates/frontend
  local filename="$2"           # e.g. siili_ai_sdk.mdc
  local src_file="$3"           # e.g. docs/.../AI_..._INSTRUCTIONS.md
  local description="$4"         # description to embed in frontmatter

  if [[ ! -d "$template_dir" ]]; then
    echo "SKIP: Template directory not found: $template_dir" >&2
    return 0
  fi

  local rules_dir="$template_dir/.cursor/rules"
  local dest_file="$rules_dir/$filename"

  write_rule "$dest_file" "$description" "$src_file"
  echo "WROTE: $dest_file"
}

# Resolve template directories (handle agent vs agents)
templates_root="$repo_root/templates"
agent_dir="$templates_root/agent"
if [[ ! -d "$agent_dir" && -d "$templates_root/agents" ]]; then
  agent_dir="$templates_root/agents"
fi

backend_template_dir="$templates_root/backend"
if [[ ! -d "$backend_template_dir" && -d "$templates_root/server" ]]; then
  backend_template_dir="$templates_root/server"
fi
frontend_template_dir="$templates_root/frontend"

# Install rules per mapping

# templates/agent(s) -> just the backend rule
install_rule_to_template \
  "$agent_dir" \
  "siili_ai_sdk.mdc" \
  "$backend_src" \
  "Cursor rules for the Agent SDK backend (Python)."

# templates/backend -> backend AND server
install_rule_to_template \
  "$backend_template_dir" \
  "siili_ai_sdk.mdc" \
  "$backend_src" \
  "Cursor rules for the Agent SDK backend (Python)."

install_rule_to_template \
  "$backend_template_dir" \
  "siili_ai_sdk_server.mdc" \
  "$server_src" \
  "Cursor rules for the Agent SDK server (FastAPI)."

# templates/frontend -> frontend
install_rule_to_template \
  "$frontend_template_dir" \
  "siili_ai_sdk.mdc" \
  "$frontend_src" \
  "Cursor rules for the Agent SDK frontend (React hooks)."

echo "Done."


