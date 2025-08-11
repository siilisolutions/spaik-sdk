#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RULES_DIR="$SCRIPT_DIR/.cursor/rules"
OUTPUT_FILE="$SCRIPT_DIR/CLAUDE.md"

uv sync

if [[ ! -d "$RULES_DIR" ]]; then
  echo "Rules directory not found: $RULES_DIR" >&2
  exit 1
fi

>"$OUTPUT_FILE"

# Concatenate all files from .cursor/rules, skipping first 5 lines of each, sorted by name
find "$RULES_DIR" -maxdepth 1 -type f -print0 | sort -z | while IFS= read -r -d '' file; do
  tail -n +6 "$file" >> "$OUTPUT_FILE"
  printf "\n" >> "$OUTPUT_FILE"
done

echo "Generated $OUTPUT_FILE from rules in $RULES_DIR"
