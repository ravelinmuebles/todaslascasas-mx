#!/usr/bin/env python3
"""
fix_recamara_pb.py
==================
Recalcula la columna `recamara_planta_baja` en la tabla `propiedades` con la
lógica de `modules.caracteristicas.extraer_caracteristicas`.  Actualiza sólo
las filas cuyo valor cambia, para minimizar escrituras.

Uso:
$ python src/fix_recamara_pb.py --batch 500
"""
import argparse
import logging
import os
import sys
from typing import List, Tuple, Optional

import psycopg2
from psycopg2.extras import execute_batch, DictCursor
from tqdm import tqdm

# Importar extractor de características
sys.path.append(os.path.dirname(__file__))
from modules.caracteristicas import extraer_caracteristicas  # type: ignore

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("fix_rec_pb")

DB_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "database": os.getenv("PG_DB", "propiedades_db"),
    "user": os.getenv("PG_USER", "pabloravel"),
    "password": os.getenv("PG_PASSWORD", ""),
    "port": int(os.getenv("PG_PORT", "5432")),
}

def detectar_rec_pb(titulo: str, descripcion: str) -> Optional[bool]:
    """Devuelve True, False o None (si no se puede determinar)."""
    texto = f"{titulo or ''} {descripcion or ''}"
    info = extraer_caracteristicas(texto)
    rec_pb = info.get("recamara_planta_baja", {})
    if isinstance(rec_pb, dict):
        return rec_pb.get("valor")
    return None

def main():
    parser = argparse.ArgumentParser(description="Recalcula recámara en planta baja")
    parser.add_argument("--batch", type=int, default=500, help="Tamaño de lote UPDATE")
    parser.add_argument("--limit", type=int, default=0, help="Máximo de filas a procesar")
    parser.add_argument("--dry-run", action="store_true", help="Sólo contabiliza cambios")
    args = parser.parse_args()

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=DictCursor)

    limit_sql = f"LIMIT {args.limit}" if args.limit else ""
    cur.execute(f"SELECT id, titulo, descripcion, recamara_planta_baja FROM propiedades {limit_sql}")
    rows = cur.fetchall()
    logger.info("Propiedades leídas: %s", len(rows))

    updates: List[Tuple] = []  # (nuevo_valor, id)
    for row in tqdm(rows, desc="Analizando", unit="prop"):
        id_prop = row["id"]
        nuevo_val = detectar_rec_pb(row["titulo"], row["descripcion"])
        if nuevo_val is None:
            continue
        if nuevo_val != row["recamara_planta_baja"]:
            updates.append((nuevo_val, id_prop))

    logger.info("Filas con cambios: %s", len(updates))
    if args.dry_run or not updates:
        logger.info("--dry-run activado o sin cambios. Fin.")
        return

    batch_size = max(1, args.batch)
    update_sql = "UPDATE propiedades SET recamara_planta_baja = %s WHERE id = %s"
    logger.info("Ejecutando UPDATE en lotes de %s…", batch_size)
    for i in tqdm(range(0, len(updates), batch_size), desc="Actualizando", unit="lote"):
        lote = updates[i : i + batch_size]
        execute_batch(cur, update_sql, lote, page_size=batch_size)
    conn.commit()
    logger.info("✅ recamara_planta_baja actualizado")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main() 