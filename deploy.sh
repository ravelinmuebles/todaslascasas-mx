#!/usr/bin/env bash
# ---------------------------------------------------------
# Script de despliegue front-end TodasLasCasas
#   • ./deploy.sh            → publica en carpeta /stg/ y crea invalidación /stg/*
#   • ./deploy.sh --prod     → publica en raíz y crea invalidación /index.html
# ---------------------------------------------------------
set -eo pipefail

DIST_ID="E2W2MQQOTU89Z"          # CloudFront distribution ID
BUCKET="todaslascasas-frontend"  # Bucket S3 público
FILE_SRC="index_s3_latest.html"  # Archivo fuente a subir

if [[ ! -f "$FILE_SRC" ]]; then
  echo "❌ No se encontró $FILE_SRC. Asegúrate de generar el build antes de desplegar."; exit 1; fi

MODE="stg"
if [[ "${1:-}" == "--prod" ]]; then MODE="prod"; fi

# ---------- TESTS BÁSICOS --------------------------------
function test_api() {
  echo "🔎 Test API health…";
  curl -sf https://api.todaslascasas.mx/health >/dev/null
  echo "✅ API health OK";

  echo "🔎 Test propiedades sin filtros…";
  local CNT=$(curl -s "https://api.todaslascasas.mx/propiedades?por_pagina=1&pagina=1" | jq '.propiedades | length')
  if [[ "$CNT" -lt 1 ]]; then echo "❌ API devolvió 0 propiedades"; exit 1; fi
  echo "✅ Propiedades OK";
}

echo "🚦 Ejecutando tests…";
if ! test_api; then
  echo "❌ Tests fallaron. Aborto despliegue."; exit 1; fi

echo "✅ Tests pasaron";

# ---------- SUBIDA A S3 ----------------------------------
TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")
if [[ "$MODE" == "prod" ]]; then
  DEST_PATH="s3://$BUCKET/index.html"
  INVALIDATE_PATH="/index.html"
else
  DEST_PATH="s3://$BUCKET/stg/index.html"
  INVALIDATE_PATH="/stg/*"
fi

# asegurarse de que la variable no contenga caracteres invisibles
INVALIDATE_CLEAN="${INVALIDATE_PATH//$'\r'/}"

echo "🚀 Subiendo $FILE_SRC a $DEST_PATH";
aws s3 cp "$FILE_SRC" "$DEST_PATH" \
  --content-type text/html \
  --cache-control "max-age=0,no-cache"

echo "🔄 Creando invalidación CloudFront $INVALIDATE_CLEAN…";
aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "$INVALIDATE_CLEAN" | head -n 15

echo "✅ Despliegue completado en modo $MODE"
if [[ "$MODE" == "stg" ]]; then
  echo "👉 URL de staging: https://todaslascasas.mx/stg/index.html?v=$TIMESTAMP"
else
  echo "👉 URL producción: https://todaslascasas.mx/index.html?v=$TIMESTAMP"
fi 