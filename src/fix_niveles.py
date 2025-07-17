#!/usr/bin/env python3
"""
fix_niveles.py
==============
Recalcula la columna `niveles` de la tabla `propiedades` usando la lógica
actualizada en modules.caracteristicas.extraer_niveles.

Corrige los casos donde se marcó «1» por la mención de «planta baja» añadiendo
reglas más precisas.

Uso:
-----
$ python src/fix_niveles.py --batch 500

Argumentos:
--batch N     Tamaño del lote UPDATE (default 500)
--limit N     Máximo de filas a procesar (útil para pruebas)
--dry-run     No escribe cambios, sólo muestra resumen
"""
import argparse
import logging
import os
import sys
from typing import List, Tuple

import psycopg2
from psycopg2.extras import execute_batch
from tqdm import tqdm

# Reutilizar lógica existente
sys.path.append(os.path.dirname(__file__))
from modules.caracteristicas import extraer_niveles  # type: ignore

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("fix_niveles")

DB_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "database": os.getenv("PG_DB", "propiedades_db"),
    "user": os.getenv("PG_USER", "pabloravel"),
    "password": os.getenv("PG_PASSWORD", ""),
    "port": int(os.getenv("PG_PORT", "5432")),
}

def detectar_niveles_texto(titulo: str, descripcion: str):
    """Wrapper alrededor de modules.caracteristicas.extraer_niveles"""
    texto = f"{titulo} {descripcion}"
    info = extraer_niveles(texto or "")
    return info.get("valor")

def main():
    parser = argparse.ArgumentParser(description="Recalcula niveles de propiedades")
    parser.add_argument("--batch", type=int, default=500, help="Tamaño de lote para UPDATE")
    parser.add_argument("--limit", type=int, default=0, help="Máximo de filas a procesar (0 = todas)")
    parser.add_argument("--dry-run", action="store_true", help="No guarda cambios, sólo muestra")
    args = parser.parse_args()

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    limit_sql = f"LIMIT {args.limit}" if args.limit else ""

    cur.execute(
        f"""
        SELECT id, titulo, descripcion, niveles
        FROM propiedades
        {limit_sql}
        """
    )
    rows = cur.fetchall()
    logger.info("Propiedades a evaluar: %s", len(rows))

    updates: List[Tuple] = []  # (nuevo_niveles, id)
    for row in tqdm(rows, desc="Reevaluando", unit="prop"):
        id_prop, titulo, descripcion, niveles_actual = row
        nuevo = detectar_niveles_texto(titulo or "", descripcion or "")

        # Si la detección es diferente al valor actual, marcar para update
        if nuevo != niveles_actual:
            updates.append((nuevo, id_prop))

    logger.info("Filas con cambios: %s", len(updates))

    if args.dry_run or not updates:
        logger.info("--dry-run activado o sin cambios, no se realizarán UPDATEs")
        return

    batch_size = max(1, args.batch)
    update_sql = "UPDATE propiedades SET niveles = %s WHERE id = %s"

    logger.info("Ejecutando UPDATEs en lotes de %s…", batch_size)
    for i in tqdm(range(0, len(updates), batch_size), desc="Actualizando", unit="lote"):
        lote = updates[i : i + batch_size]
        execute_batch(cur, update_sql, lote, page_size=batch_size)
    conn.commit()
    logger.info("✅ Niveles corregidos y confirmados")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main() 