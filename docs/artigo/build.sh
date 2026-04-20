#!/usr/bin/env bash
# Build dos artigos PDF a partir dos HTMLs via WeasyPrint.
# PDFs são gerados em ~/Downloads (fora do repo).
#
# Uso: bash docs/artigo/build.sh [--out DIR]
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="${HOME}/Downloads"

# Override via --out
if [[ "${1:-}" == "--out" && -n "${2:-}" ]]; then
  OUT_DIR="$2"
fi
mkdir -p "$OUT_DIR"

if ! command -v weasyprint >/dev/null 2>&1; then
  echo "weasyprint não instalado. Rodar: pip install weasyprint"
  exit 1
fi

for html in "$DIR"/*.html; do
  base="$(basename "$html" .html)"
  pdf="$OUT_DIR/$base.pdf"
  echo "→ $pdf"
  weasyprint "$html" "$pdf" 2>/dev/null || weasyprint "$html" "$pdf"
done

echo ""
echo "PDFs gerados em: $OUT_DIR"
ls -lh "$OUT_DIR"/vila_inteia*.pdf 2>&1 | awk '{printf "  %s  %s\n", $5, $9}'
