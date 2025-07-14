#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Actualiza la columna `recamaras` de la tabla `propiedades` buscando la cantidad
máxima de recámaras mencionada en título y descripción.

• Usa los patrones de src/modules/caracteristicas.extraer_recamaras.
• Sólo actualiza si el valor detectado es distinto y válido (1-10).
• Modo --dry-run para reportar sin modificar.

Ejemplo:
  python update_recamaras_db.py            # actualiza BD
  python update_recamaras_db.py --dry-run  # solo estadísticas
"""

import argparse
import logging
import re
from typing import Optional
import psycopg2
from psycopg2.extras import DictCursor

# ---------------------------------------------------------------------------
# Configuración DB (mismos datos que Lambda)
# ---------------------------------------------------------------------------
DB_CONFIG = {
    'host': 'todaslascasas-postgres.cqpcyeqa0uqj.us-east-1.rds.amazonaws.com',
    'database': 'propiedades_db',
    'user': 'pabloravel',
    'password': 'Todaslascasas2025',
    'port': 5432
}

# ---------------------------------------------------------------------------
# Patrones para detectar recámaras (idénticos a caracteristicas.py)
# ---------------------------------------------------------------------------
RECAMARAS_PATTERNS = [
    r"(\d+)\s*(?:recámaras?|recamaras?|rec\.?|habitaciones?|cuartos?)",
    r"(?:recámaras?|recamaras?|rec\.?|habitaciones?|cuartos?)\s*(\d+)"
]

def detectar_recamaras(texto: str) -> Optional[int]:
    """Devuelve la mayor cantidad de recámaras encontrada (1-10)"""
    if not texto:
        return None
    texto_norm = texto.lower()
    encontrados = []
    for patron in RECAMARAS_PATTERNS:
        for match in re.findall(patron, texto_norm):
            try:
                val = int(match)
                if 1 <= val <= 10:
                    encontrados.append(val)
            except ValueError:
                continue
    return max(encontrados) if encontrados else None


def main():
    parser = argparse.ArgumentParser(description="Actualiza columna recamaras en BD")
    parser.add_argument('--dry-run', action='store_true', help='Solo reporte, sin UPDATE')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    conn = psycopg2.connect(**DB_CONFIG)
    cur: DictCursor = conn.cursor(cursor_factory=DictCursor)

    # Seleccionar propiedades con recamaras NULL o 0
    cur.execute("""
        SELECT id, titulo, descripcion, recamaras
        FROM propiedades
        WHERE recamaras IS NULL OR recamaras = 0
    """)
    rows = cur.fetchall()
    logging.info("Propiedades a revisar: %d", len(rows))

    actualizados = 0
    for row in rows:
        prop_id, titulo, descripcion, rec_actual = row
        texto = f"{titulo or ''} {descripcion or ''}"
        rec_detect = detectar_recamaras(texto)
        if rec_detect and rec_detect != rec_actual:
            logging.debug("ID %s: %s -> %s", prop_id, rec_actual, rec_detect)
            if not args.dry_run:
                cur.execute("UPDATE propiedades SET recamaras = %s WHERE id = %s", (rec_detect, prop_id))
            actualizados += 1

    if not args.dry_run:
        conn.commit()
    cur.close()
    conn.close()

    logging.info("Actualizaciones aplicadas: %d", actualizados)
    if args.dry_run:
        logging.info("Ejecución en modo DRY RUN: no se realizaron cambios en la BD")

if __name__ == "__main__":
    main() 