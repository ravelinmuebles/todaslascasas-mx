#!/usr/bin/env python3
"""
actualiza_autores_db.py
──────────────────────
• Recorre el repositorio maestro de propiedades.
• Para cada propiedad sin campo "autor" intenta extraerlo del HTML ya guardado.
• Si se encuentra, actualiza:
    – El JSON maestro (resultados/repositorio_propiedades.json)
    – La base de datos PostgreSQL (tabla `propiedades`, columna `autor`) si no está en DRY_RUN.

Uso rápido:
    DRY_RUN=1 LIMIT=50 python3 src/actualiza_autores_db.py
Variables de entorno:
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS  → credenciales PostgreSQL.
    LIMIT        → Nº máx de propiedades a procesar (0 = sin límite).
    DRY_RUN      → 1/true/yes → solo modifica JSON, no BD.
"""
from __future__ import annotations
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Any

try:
    import psycopg2  # type: ignore
except ImportError:
    psycopg2 = None  # Se avisa después si se requiere

# ── Constantes ────────────────────────────────────────────────────────────────
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
CARPETA_RESULTADOS = RAIZ_PROYECTO / "resultados"
PATH_REPO_MASTER = CARPETA_RESULTADOS / "repositorio_propiedades.json"

# Valores por defecto según bitácora del proyecto (RDS)
DEFAULT_DB_HOST = "todaslascasas-postgres.cqpcyeqa0uqj.us-east-1.rds.amazonaws.com"
DEFAULT_DB_NAME = "propiedades_db"
DEFAULT_DB_PORT = "5432"
DEFAULT_DB_USER = "pabloravel"

# Regex de extracción de autor (mismos patrones del scraper principal)
autor_regex_v1 = re.compile(
    r'"link_url":"https:\\/\\/www\\.facebook\\.com\\/profile\\.php\\?id=[^"\\]+"[^}]*?"title":"([^"\\]+)"'
)
autor_regex_v2 = re.compile(
    r'marketplace_listing_seller":\\?\{.*?"name":"([^"\\]+)"',
    re.DOTALL,
)


# ── Utilidades ───────────────────────────────────────────────────────────────

def extraer_autor(html: str) -> str:
    """Devuelve el nombre del autor si se encuentra en el HTML."""
    m = autor_regex_v1.search(html) or autor_regex_v2.search(html)
    if not m:
        return ""
    raw = m.group(1)
    try:
        return bytes(raw, "latin1").decode("unicode_escape")
    except Exception:
        return raw


def cargar_repo_master() -> Dict[str, Any]:
    if not PATH_REPO_MASTER.exists():
        print(f"❌ No se encontró {PATH_REPO_MASTER}")
        sys.exit(1)
    with open(PATH_REPO_MASTER, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_repo_master(data: Dict[str, Any]):
    tmp = PATH_REPO_MASTER.with_suffix(".tmp.json")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(PATH_REPO_MASTER)


def connect_db():
    if psycopg2 is None:
        raise RuntimeError("psycopg2 no instalado. Instálalo o ejecuta con DRY_RUN=1")
    # Recuperar parámetros de entorno o usar defaults del proyecto
    params = {
        "host": os.getenv("DB_HOST", DEFAULT_DB_HOST),
        "port": os.getenv("DB_PORT", DEFAULT_DB_PORT),
        "dbname": os.getenv("DB_NAME", DEFAULT_DB_NAME),
        "user": os.getenv("DB_USER", DEFAULT_DB_USER),
        "password": os.getenv("DB_PASS", ""),
    }

    # Si falta password, intentar obtenerlo de Secrets Manager (aws cli)
    if not params["password"]:
        secret_name = os.getenv("DB_SECRET_NAME", "todaslascasas-postgres-credentials")
        try:
            import json as _json
            import subprocess, shlex
            cmd = f"aws secretsmanager get-secret-value --secret-id {secret_name} --query SecretString --output text"
            result = subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                secret_dict = _json.loads(result.stdout.strip())
                params["password"] = secret_dict.get("password") or secret_dict.get("PGPASSWORD") or ""
        except Exception:
            pass

    if not params["password"]:
        raise RuntimeError("No se pudo determinar la contraseña para la BD. Define DB_PASS o configura Secrets Manager.")

    return psycopg2.connect(**params)


def actualizar_db(conn, pid: str, autor: str):
    with conn.cursor() as cur:
        cur.execute("UPDATE propiedades SET autor=%s WHERE id=%s", (autor, pid))
    conn.commit()

# --- DDL helper -------------------------------------------------------------

def ensure_columna_autor(conn):
    """Crea la columna autor en la tabla propiedades si no existe."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name='propiedades' AND column_name='autor'
            """
        )
        if cur.fetchone() is None:
            print("🛠️  Añadiendo columna 'autor' a la tabla propiedades …")
            cur.execute("ALTER TABLE propiedades ADD COLUMN autor text")
            conn.commit()
            print("✅ Columna 'autor' creada")


# ── Programa principal ───────────────────────────────────────────────────────

def main():
    limit = int(os.getenv("LIMIT", "0"))
    dry_run = os.getenv("DRY_RUN", "0").lower() in ("1", "true", "yes")

    data = cargar_repo_master()
    ids_sin_autor = [pid for pid, v in data.items() if not v.get("autor")]

    if limit:
        ids_sin_autor = ids_sin_autor[:limit]

    if not ids_sin_autor:
        print("✅ No hay propiedades pendientes de autor.")
        return

    print(f"🔍 Procesando {len(ids_sin_autor)} propiedades sin autor (DRY_RUN={'YES' if dry_run else 'NO'})")

    conn = None
    if not dry_run:
        try:
            conn = connect_db()
            ensure_columna_autor(conn)
        except Exception as e:
            print(f"❌ Error conectando a BD: {e}. Ejecuta con DRY_RUN=1 o configura las variables de entorno.")
            return

    actualizados = 0
    for pid in ids_sin_autor:
        registro = data[pid]
        ruta_html_rel = registro.get("archivos", {}).get("html")
        if not ruta_html_rel:
            continue
        ruta_html = CARPETA_RESULTADOS / ruta_html_rel
        if not ruta_html.exists():
            # Buscar en subdirectorios con el mismo nombre de archivo
            coincidencias = list(CARPETA_RESULTADOS.rglob(ruta_html_rel))
            if coincidencias:
                ruta_html = coincidencias[0]
            else:
                print(f"⚠️  HTML no encontrado para {pid} → {ruta_html_rel}")
                continue
        try:
            html = ruta_html.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"⚠️  Error leyendo HTML {pid}: {e}")
            continue

        autor = extraer_autor(html)
        if autor:
            registro["autor"] = autor
            actualizados += 1
            print(f"✓ {pid}: {autor}")
            if conn is not None:
                try:
                    actualizar_db(conn, pid, autor)
                except Exception as e:
                    print(f"❌  Error BD en {pid}: {e}")
        else:
            print(f"— {pid}: autor no encontrado")

    if actualizados:
        guardar_repo_master(data)
        print(f"💾 JSON maestro actualizado ({actualizados} registros)")
    else:
        print("ℹ️  No se actualizó ningún registro")

    if conn:
        # Sincronizar registros que YA tienen autor si se solicita
        if os.getenv("SYNC_DB_EXISTING", "0").lower() in ("1", "true", "yes"):
            print("⇆ Sincronizando autores ya existentes con la BD …")
            pendientes_db = [
                (v["autor"], pid)
                for pid, v in data.items()
                if v.get("autor")
            ]
            with conn.cursor() as cur:
                cur.executemany(
                    "UPDATE propiedades SET autor=%s WHERE id=%s AND (autor IS NULL OR autor='')",
                    pendientes_db,
                )
            conn.commit()
            print(f"✅ Sincronizados {len(pendientes_db)} registros con la BD")

        conn.close()
        print("🔗 Conexión BD cerrada")


if __name__ == "__main__":
    main() 