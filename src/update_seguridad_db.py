#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_seguridad_db.py
======================
Recalcula y actualiza indicadores de seguridad en la tabla `propiedades`:
    • caseta_vigilancia (bool)
    • camaras_seguridad (bool)
    • vigilancia_24h   (bool)
    • acceso_controlado(bool)

Se basa en patrones de `modules/seguridad.py` (o copia dentro de Lambda).

Uso:
    python update_seguridad_db.py            # ejecuta actualización
    python update_seguridad_db.py --dry-run  # muestra totales sin modificar BD
"""
import argparse
import logging
import psycopg2
from psycopg2.extras import DictCursor
from pathlib import Path
import sys

# Permitir importar módulos del proyecto
ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT / 'modules'))

from seguridad import extraer_seguridad

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

DB_CFG = dict(
    host="todaslascasas-postgres.cqpcyeqa0uqj.us-east-1.rds.amazonaws.com",
    database="propiedades_db",
    user="pabloravel",
    port=5432,
)

CAMPOS = [
    "caseta_vigilancia",
    "camaras_seguridad",
    "vigilancia_24h",
    "acceso_controlado",
]

def main(dry_run: bool = False):
    conn = psycopg2.connect(**DB_CFG)
    cur = conn.cursor(cursor_factory=DictCursor)
    logging.info("Leyendo propiedades…")
    cur.execute("SELECT id, titulo, descripcion, amenidades, " + ", ".join(CAMPOS) + " FROM propiedades")
    filas = cur.fetchall()
    logging.info("Propiedades leídas: %d", len(filas))

    updates = []
    for row in filas:
        id_prop = row[0]
        titulo = row[1] or ""
        descripcion = row[2] or ""
        amenidades = row[3]
        if amenidades is None:
            amenidades_txt = ""
        else:
            amenidades_txt = ",".join(amenidades) if isinstance(amenidades, list) else str(amenidades)

        texto = f"{titulo} {descripcion} {amenidades_txt}"
        indicadores = extraer_seguridad(texto)

        cambios = {
            campo: indicadores[campo] for campo in CAMPOS if indicadores[campo] != bool(row[4 + CAMPOS.index(campo)])
        }
        if cambios:
            updates.append((id_prop, cambios))

    logging.info("Filas con cambios: %d", len(updates))
    if dry_run:
        logging.info("--dry-run activo: no se realizarán actualizaciones")
        conn.close()
        return

    # Ejecutar updates
    for id_prop, cambios in updates:
        set_clause = ", ".join([f"{campo} = %s" for campo in cambios.keys()])
        valores = list(cambios.values())
        valores.append(id_prop)
        sql = f"UPDATE propiedades SET {set_clause} WHERE id = %s"
        cur.execute(sql, valores)
    conn.commit()
    logging.info("Actualización completada: %d filas modificadas", len(updates))
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Actualiza indicadores de seguridad en la BD")
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar cuántas filas se modificarían")
    args = parser.parse_args()
    main(dry_run=args.dry_run) 