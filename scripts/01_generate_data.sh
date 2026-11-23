#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[1/3] Generating medium-scale BigQuery CSV datasets & Antigravity sample batch CSV..."
python3 "$ROOT_DIR/data_generators/generate_bq_data.py"

echo "[2/3] Generating GCS enterprise documents (HTML & OOXML XLSX)..."
python3 "$ROOT_DIR/data_generators/generate_gcs_docs.py"

echo "[3/3] Running local Antigravity sample batch validator check..."
python3 "$ROOT_DIR/agy_workspace/samples/batch_copy_validator.py"

echo "Done. Generated datasets under: $ROOT_DIR/generated_data/"
