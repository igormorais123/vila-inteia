#!/usr/bin/env bash
# Build do PDF acadêmico a partir do HTML via WeasyPrint.
# Uso: bash docs/artigo/build.sh
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HTML="$DIR/vila_inteia_artigo.html"
PDF="$DIR/vila_inteia_artigo.pdf"

if ! command -v weasyprint >/dev/null 2>&1; then
  echo "weasyprint não instalado. Rodar: pip install weasyprint"
  exit 1
fi

weasyprint "$HTML" "$PDF"
echo "PDF gerado: $PDF"
ls -lh "$PDF"
