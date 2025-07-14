#!/usr/bin/env python3
"""
backfill_nuevas_columnas.py
===========================
Rellena las columnas recientemente añadidas a la tabla `propiedades`:
    - niveles (INT)
    - recamara_pb (BOOLEAN)
    - caseta_vigilancia (BOOLEAN)
    - camaras_seguridad (BOOLEAN)
    - vigilancia_24h (BOOLEAN)
    - acceso_controlado (BOOLEAN)

Características:
1.   --dry-run  : No escribe en la BD, sólo muestra estadísticos.
2.   --limit N  : Procesa máximo N registros (para pruebas).
3.   --batch N  : Tamaño de lote para UPDATEs.
4.   Usa las mismas funciones de detección empleadas en la Lambda
     (`detectar_niveles` y `actualizar_seguridad`).

Uso:
$ python src/backfill_nuevas_columnas.py --dry-run --limit 1000
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
from modules.seguridad import actualizar_seguridad           # type: ignore

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("backfill")

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

def procesar_registro(row) -> Tuple[int, int, bool, bool, bool, bool]:
    """Devuelve (niveles, rec_pb, caseta, camaras, vig24, acceso)"""
    (
        id_prop,
        titulo,
        descripcion,
        niveles_actual,
        rec_pb_actual,
        caseta_actual,
        camaras_actual,
        vig24_actual,
        acceso_actual,
    ) = row

    # ─── Detectar niveles ──────────────────────────────────────────────
    niveles_nuevo = niveles_actual
    if niveles_actual is None:
        niveles_nuevo = detectar_niveles_texto(titulo or "", descripcion or "")

    # ─── Seguridad ────────────────────────────────────────────────────
    seguridad_dict = {
        "caseta_vigilancia": caseta_actual,
        "camaras_seguridad": camaras_actual,
        "vigilancia_24h": vig24_actual,
        "acceso_controlado": acceso_actual,
    }
    prop_stub = {
        "descripcion": descripcion,
        "titulo": titulo,
        **seguridad_dict,
    }
    prop_stub = actualizar_seguridad(prop_stub)

    return (
        niveles_nuevo,
        prop_stub.get("recamara_planta_baja"),
        prop_stub.get("caseta_vigilancia"),
        prop_stub.get("camaras_seguridad"),
        prop_stub.get("vigilancia_24h"),
        prop_stub.get("acceso_controlado"),
    )

def main():
    parser = argparse.ArgumentParser(description="Backfill nuevas columnas propiedades")
    parser.add_argument("--dry-run", action="store_true", help="No guarda cambios")
    parser.add_argument("--limit", type=int, default=0, help="Máximo de filas a procesar")
    parser.add_argument("--batch", type=int, default=500, help="Tamaño de lote para UPDATE")
    args = parser.parse_args()

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    limit_sql = f"LIMIT {args.limit}" if args.limit else ""

    cur.execute(
        f"""
        SELECT id, titulo, descripcion, niveles, recamara_planta_baja, caseta_vigilancia,
               camaras_seguridad, vigilancia_24h, acceso_controlado
        FROM propiedades
        WHERE (
            niveles IS NULL
            OR recamara_planta_baja IS NULL
            OR caseta_vigilancia IS NULL
            OR camaras_seguridad IS NULL
            OR vigilancia_24h IS NULL
            OR acceso_controlado IS NULL
        )
        {limit_sql}
        """
    )
    rows = cur.fetchall()
    logger.info("Propiedades a evaluar: %s", len(rows))

    updates: List[Tuple] = []
    for row in tqdm(rows, desc="Procesando", unit="prop"):
        id_prop = row[0]
        nuevos = procesar_registro(row)
        if any(v is not None for v in nuevos):
            updates.append((*nuevos, id_prop))

    logger.info("Filas con cambios: %s", len(updates))

    if args.dry_run or not updates:
        logger.info("--dry-run activado, no se realizarán UPDATEs")
        return

    batch_size = max(1, args.batch)
    update_sql = (
        "UPDATE propiedades SET "
        "niveles = COALESCE(%s, niveles), "
        "recamara_planta_baja = COALESCE(%s, recamara_planta_baja), "
        "caseta_vigilancia = COALESCE(%s, caseta_vigilancia), "
        "camaras_seguridad = COALESCE(%s, camaras_seguridad), "
        "vigilancia_24h = COALESCE(%s, vigilancia_24h), "
        "acceso_controlado = COALESCE(%s, acceso_controlado) "
        "WHERE id = %s"
    )

    logger.info("Ejecutando UPDATEs en lotes de %s…", batch_size)
    for i in tqdm(range(0, len(updates), batch_size), desc="Actualizando", unit="lote"):
        lote = updates[i:i+batch_size]
        execute_batch(cur, update_sql, lote, page_size=batch_size)
    conn.commit()
    logger.info("✅ Backfill completado y confirmado")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main() 