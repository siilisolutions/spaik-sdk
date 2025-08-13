#!/usr/bin/env bash
set -euo pipefail

# Run in the directory where this script resides
cd "$(dirname "$0")"

# Make globs return empty when no match and be case-insensitive (so *.md matches *.MD)
shopt -s nullglob nocaseglob

found_any=false

for md_file in *.md; do
    found_any=true
    pdf_file="${md_file%.md}.pdf"
    echo "Converting: $md_file -> $pdf_file"
    md2pdf "$md_file" "$pdf_file"
done

if [ "$found_any" = false ]; then
    echo "No markdown files found in $(pwd)"
fi


