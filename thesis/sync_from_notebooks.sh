#!/bin/bash
# Sync appendix tables and figures from the MAS notebook outputs.
# Run this from the Thesis/ folder before compiling, or include it in the
# pdflatex build command.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_ROOT="$SCRIPT_DIR/.."
DST_ROOT="$SCRIPT_DIR"

echo "Syncing appendix tables..."
mkdir -p "$DST_ROOT/appendix/tables"
rsync -av --delete \
  --include='02_*.csv' \
  --include='03_*.csv' \
  --exclude='*' \
  "$SRC_ROOT/notebooks/tables/" \
  "$DST_ROOT/appendix/tables/"

echo "Syncing appendix figures..."
mkdir -p "$DST_ROOT/appendix/figures"
rsync -av --delete \
  --exclude='.*' \
  "$SRC_ROOT/notebooks/figures/" \
  "$DST_ROOT/appendix/figures/"

echo "Regenerating CSV-backed appendix tables..."
python3 "$DST_ROOT/generate_appendix_tables.py"

echo "Appendix sync complete."
