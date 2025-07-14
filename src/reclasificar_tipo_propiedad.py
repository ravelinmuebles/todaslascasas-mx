#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RECLASIFICACIÓN MASIVA DE TIPO DE PROPIEDAD
==========================================

• Lee todas las propiedades cuyo tipo_propiedad sea Bodega/Oficina/Local, etc.
• Vuelve a ejecutar la detección inteligente (`modules.tipo_propiedad.actualizar_tipo_propiedad`).
• Si el tipo detectado difiere, actualiza la fila en PostgreSQL.
• Genera un resumen al final.

USO:
    python reclasificar_tipo_propiedad.py --host ... --db ... --user ... --port 5432

Requiere variable de entorno `PGPASSWORD` para la contraseña.
"""

import argparse
import json
from datetime import datetime
from typing import Dict

import psycopg2
from psycopg2.extras import RealDictCursor

from modules import tipo_propiedad as tp


def procesar_propiedad(row: Dict) -> str:
    """Detecta de nuevo tipo_propiedad y devuelve el nuevo valor o el existente."""
    updated = tp.actualizar_tipo_propiedad(row.copy())  # no mutar original de psycopg2
    return updated.get("tipo_propiedad") or row.get("tipo_propiedad")


def main(args):
    conn = psycopg2.connect(
        host=args.host,
        database=args.database,
        user=args.user,
        port=args.port,
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)

    objetivo = tuple([s.lower() for s in ["bodega", "oficina", "local", "comercial", "desconocido"]])

    query_base = (
        "SELECT id, titulo, descripcion, tipo_propiedad "
        "FROM propiedades WHERE LOWER(tipo_propiedad) IN %s"
    )
    params = [objetivo]

    if args.limit:
        query_base += " LIMIT %s"
        params.append(args.limit)

    cur.execute(query_base, tuple(params))
    rows = cur.fetchall()

    total = len(rows)
    cambiados = 0

    print(f"🔍 Analizando {total} propiedades potencialmente mal clasificadas…")

    for row in rows:
        id_prop = row["id"]
        nuevo_tipo = procesar_propiedad(row)
        actual = row.get("tipo_propiedad")
        if nuevo_tipo and nuevo_tipo.lower() != (actual or "").lower():
            if not args.dry_run:
                cur.execute(
                    "UPDATE propiedades SET tipo_propiedad = %s WHERE id = %s",
                    (nuevo_tipo.lower(), id_prop),
                )
            cambiados += 1
            if cambiados % 100 == 0:
                print(f"  → {cambiados} detectados para actualización…")

    if not args.dry_run:
        conn.commit()
    cur.close()
    conn.close()

    print("✅ Reclasificación completada")
    print(f"   Total inspeccionados: {total}")
    print(f"   Total actualizados : {cambiados}")
    print(f"   Fecha: {datetime.utcnow().isoformat()}Z")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--database", default="propiedades_db")
    parser.add_argument("--user", default="pabloravel")
    parser.add_argument("--port", type=int, default=5432)
    parser.add_argument("--limit", type=int, help="Procesar solo N filas (debug)")
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar cambios, no actualizar")
    args = parser.parse_args()
    main(args) 