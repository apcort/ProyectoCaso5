#!/usr/bin/env bash
# Crea carpetas de prueba para no tocar nunca / ni la carpeta personal completa.
set -euo pipefail

BASE="${1:-$HOME/respaldos_prueba}"
ORIGEN="$BASE/origen_web"
DESTINO="$BASE/destino"

mkdir -p "$ORIGEN/css" "$ORIGEN/img" "$DESTINO"
echo "<html><body>Hola</body></html>" > "$ORIGEN/index.html"
echo "body { color: navy; }" > "$ORIGEN/css/estilo.css"
head -c 200000 /dev/urandom > "$ORIGEN/img/logo.bin"

for i in 1 2 3; do
    echo "Pagina $i" > "$ORIGEN/pagina$i.html"
done

echo "Carpetas de prueba creadas:"
echo " origen : $ORIGEN"
echo " destino: $DESTINO"
