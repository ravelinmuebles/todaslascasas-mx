#!/usr/bin/env python3
"""Backfill de tipo_propiedad (local, oficina, etc.) en registros antiguos.

Corre en lotes para no saturar la BD. Lee las filas cuyo tipo_propiedad
esté vacío, sea NULL o igual a 'comercial/otro', calcula de nuevo el tipo
usando modules.tipo_propiedad.actualizar_tipo_propiedad y actualiza la BD
si detecta un valor diferente.

Se ejecuta con:
    make backfill-tipo-prop

Usa las mismas variables de entorno del API para conectarse a PostgreSQL.
"""

import os
import sys
import logging
from typing import Dict
import pg8000

# Añadir src/ al path para importar modules.*
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_DIR = os.path.join(ROOT_DIR, 'src')
sys.path.append(SRC_DIR)

from modules.tipo_propiedad import actualizar_tipo_propiedad  # type: ignore

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("backfill_tipo_propiedad")

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'todaslascasas-postgres.cqpcyeqa0uqj.us-east-1.rds.amazonaws.com'),
    'database': os.environ.get('DB_NAME', 'propiedades_db'),
    'user': os.environ.get('DB_USER', 'pabloravel'),
    'password': os.environ.get('DB_PASSWORD', 'Todaslascasas2025'),
    'port': int(os.environ.get('DB_PORT', 5432))
}

BATCH_SIZE = 500


def get_conn():
    return pg8000.connect(**DB_CONFIG)


def process_row(row: Dict) -> str:
    """Retorna tipo detectado (o fila existente)"""
    prop = {
        'titulo': row.get('titulo') or '',
        'descripcion': row.get('descripcion') or ''
    }
    resultado = actualizar_tipo_propiedad(prop)
    return resultado.get('tipo_propiedad')


def main():
    conn = get_conn()
    cursor = conn.cursor()
    total_actualizados = 0
    while True:
        cursor.execute(
            """
            SELECT id, titulo, descripcion, tipo_propiedad
            FROM propiedades
            WHERE LOWER(COALESCE(tipo_propiedad, '')) IN ('', 'comercial', 'otro', 'casa')
            LIMIT %s
            """,
            (BATCH_SIZE,)
        )
        rows = cursor.fetchall()
        if not rows:
            break
        columnas = [d[0] for d in cursor.description]
        actualizados = 0
        for raw in rows:
            row = dict(zip(columnas, raw))
            nuevo_tipo = process_row(row)
            if nuevo_tipo and nuevo_tipo not in ('', 'comercial', 'otro'):
                cursor.execute(
                    "UPDATE propiedades SET tipo_propiedad=%s WHERE id=%s",
                    (nuevo_tipo, row['id'])
                )
                actualizados += 1
        conn.commit()
        total_actualizados += actualizados
        logger.info(f"📝 Batch procesado: {actualizados} registros actualizados")
        if len(rows) < BATCH_SIZE:
            break
    logger.info(f"✅ Backfill completado. Total registros actualizados: {total_actualizados}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("Proceso interrumpido por el usuario") 