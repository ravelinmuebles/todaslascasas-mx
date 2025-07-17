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
from pg8000.exceptions import InterfaceError
from importlib import import_module

# Añadir src/ al path para importar modules.*
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_DIR = os.path.join(ROOT_DIR, 'src')
sys.path.append(SRC_DIR)

from modules.tipo_propiedad import actualizar_tipo_propiedad  # type: ignore

# Wrapper para reutilizar el detector existente sin duplicar lógica
tipo_mod = import_module('modules.tipo_propiedad')


def detectar_nuevo_tipo(titulo: str, descripcion: str) -> str:
    texto = f"{titulo or ''} {descripcion or ''}"
    return tipo_mod.detectar_tipo_por_descripcion(texto) or ''

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("backfill_tipo_propiedad")

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'todaslascasas-postgres.cqpcyeqa0uqj.us-east-1.rds.amazonaws.com'),
    'database': os.environ.get('DB_NAME', 'propiedades_db'),
    'user': os.environ.get('DB_USER', 'pabloravel'),
    'password': os.environ.get('DB_PASSWORD', 'Todaslascasas2025'),
    'port': int(os.environ.get('DB_PORT', 5432))
}

# Tamaño de lote y pausa reconexión
BATCH_SIZE = 500

def count_target(cur):
    cur.execute("SELECT COUNT(*) FROM propiedades WHERE LOWER(COALESCE(tipo_propiedad, '')) IN ('', 'comercial', 'otro', 'casa')")
    return cur.fetchone()[0]

def print_progress(done,total):
    pct = done*100/total if total else 100
    bar_len = 20
    filled = int(bar_len*pct/100)
    bar = '█'*filled + '-'*(bar_len-filled)
    print(f"\rProgreso: |{bar}| {pct:.1f}% ({done}/{total})", end='', flush=True)


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


def fetch_batch(cur, offset):
    cur.execute(
        """
        SELECT id, titulo, descripcion, tipo_propiedad
        FROM propiedades
        WHERE LOWER(COALESCE(tipo_propiedad, '')) IN ('', 'comercial', 'otro', 'casa')
        ORDER BY id
        LIMIT %s OFFSET %s
        """,
        (BATCH_SIZE, offset),
    )
    return cur.fetchall()


def main():
    conn = get_conn()
    cur = conn.cursor()
    total_rows = count_target(cur)
    offset = 0
    total_updated = 0
    try:
        while True:
            batch = fetch_batch(cur, offset)
            if not batch:
                break
            for row in batch:
                pid, titulo, descripcion, tipo_actual = row
                nueva = detectar_nuevo_tipo(titulo, descripcion)
                if nueva and nueva != tipo_actual:
                    cur.execute(
                        "UPDATE propiedades SET tipo_propiedad=%s WHERE id=%s",
                        (nueva, pid),
                    )
                    total_updated += 1
            conn.commit()
            offset += BATCH_SIZE
            print_progress(offset if offset<total_rows else total_rows, total_rows)
            logging.debug(f"📝 Batch offset {offset} – acumulados: {total_updated}")
    except InterfaceError:
        logging.error("Conexión perdida; reinicia y continúa con offset %s", offset)
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("Proceso interrumpido por el usuario") 