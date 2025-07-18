#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extrae_html_con_operacion.py

Versión mejorada de extracción de Facebook Marketplace,
con mejoras en la detección de tipo de operación, ubicación
y características de las propiedades.
"""

import os
import json
import requests
import time
import re
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
import subprocess
import sys
from src.modules.direccion_completa import extract_address_from_html  # Nueva función de dirección precisa

# Barra de progreso (idéntica a la tuya)
class ProgressBar:
    MAGENTA = "\033[35m"
    RESET   = "\033[0m"
    def __init__(self, total, desc='', unit=''):
        self.total = total; self.n = 0; self.ok = 0; self.err = 0
        self.last_time = 0.0; self.desc = desc; self.unit = unit
        self.length = 40; self.start_time = time.time(); self._print()
    def _print(self):
        filled = int(self.length * self.n / self.total) if self.total else self.length
        bar    = '█' * filled + '-' * (self.length - filled)
        pct    = (self.n / self.total * 100) if self.total else 100
        faltan = self.total - self.n
        print(f"\r{self.desc}: {pct:3.0f}%|"
              f"{self.MAGENTA}{bar}{self.RESET}| "
              f"{self.n}/{self.total}  Faltan: {faltan} de {self.total}  "
              f"[ok={self.ok}, err={self.err}, t={self.last_time:.2f}s]",
              end='', flush=True)
    def update(self, n=1, ok=None, err=None, last_time=None):
        self.n += n
        if ok       is not None: self.ok = ok
        if err      is not None: self.err = err
        if last_time is not None: self.last_time = last_time
        self._print()
    def close(self):
        print()

# ── Rutas y constantes ────────────────────────────────────────────────
CARPETA_LINKS       = "resultados/links/repositorio_unico.json"  # ✅ Repositorio legacy unificado
CARPETA_RESULTADOS  = os.path.abspath(os.path.join(os.path.dirname(__file__), "resultados"))
CARPETA_REPO_MASTER = os.path.join(CARPETA_RESULTADOS, "repositorio_propiedades.json")
ESTADO_FB           = "fb_state.json"
BASE_URL            = "https://www.facebook.com"

# ──  FLAGS DE EJECUCIÓN OPCIONALES  ─────────────────────────────────────
#  RECHECK_ALL=1            → Vuelve a visitar **todos** los links del repositorio, sin filtrar por maestro.
#  REMOVE_NOT_AVAILABLE=1   → Cuando detecta que una publicación ya no existe en Facebook la elimina tanto
#                              del repositorio maestro como del archivo de links, para no revisitarla.

RECHECK_ALL           = os.getenv("RECHECK_ALL", "0").lower() not in ("0", "", "false", "no")
# Por defecto SÍ elimina publicaciones que ya no existen; se puede desactivar con REMOVE_NOT_AVAILABLE=0
REMOVE_NOT_AVAILABLE  = os.getenv("REMOVE_NOT_AVAILABLE", "1").lower() not in ("0", "", "false", "no")

# ── Funciones de extracción ────────────────────────────────────────────
def extraer_descripcion_estable(soup):
    for div in soup.find_all("div"):
        if div.get_text(strip=True) in ["Descripción", "Detalles"]:
            siguiente = div.find_next_sibling("div")
            if siguiente:
                return siguiente.get_text(separator="\n", strip=True).replace("Ver menos","").strip()
    return ""

def procesar_numero_mexicano(numero):
    """Procesa números en formato mexicano y retorna float o None"""
    if not numero:
        return None
    try:
        # Remover $ y espacios y /mes
        limpio = re.sub(r'[^\d\.,]', '', numero)
        
        # En México: punto = separador de miles, coma = decimal
        if ',' in limpio and '.' in limpio:
            # Formato: 1.500.000,50 -> 1500000.50
            partes = limpio.split(',')
            entero = partes[0].replace('.', '')
            decimal = partes[1] if len(partes) > 1 else '0'
            return float(entero + '.' + decimal)
        elif '.' in limpio:
            # Solo puntos - probablemente separadores de miles
            if limpio.count('.') > 1 or len(limpio.split('.')[-1]) > 2:
                # Múltiples puntos o último grupo > 2 dígitos = separadores de miles
                return float(limpio.replace('.', ''))
            else:
                # Un solo punto con 1-2 dígitos después = decimal
                return float(limpio)
        else:
            # Solo números o comas
            return float(limpio.replace(',', '.'))
    except:
        return None


def validar_precio(valor, tipo_operacion=None):
    """Valida solo que el precio se procesó correctamente (sin restricciones)"""
    if not valor or valor <= 0:
        return False, 0.0, "Precio inválido o cero"
    
    # Precio procesado correctamente - VÁLIDO (sin restricciones por tipo)
    return True, 0.9, None
def extraer_precio(soup):
    """
    Función simple y confiable de extracción de precio (del script anterior).
    """
    for span in soup.find_all("span"):
        texto = span.get_text(strip=True)
        if texto.startswith("$") and len(texto) < 30:
            return texto
    return ""

def extraer_precio_mejorado(soup):
    """
    Función mejorada que extrae el precio y preserva contexto de /mes
    """
    # Buscar en spans que contengan precios
    for span in soup.find_all("span"):
        texto = span.get_text(strip=True)
        if texto.startswith("$") and len(texto) < 50:
            # Buscar contexto de "/mes" en el mismo span o en spans cercanos
            texto_completo = texto
            
            # Buscar /mes en el mismo span
            if "/mes" in texto:
                return texto
            
            # Buscar /mes en spans hermanos
            parent = span.parent
            if parent:
                texto_parent = parent.get_text(strip=True)
                if "/mes" in texto_parent:
                    return f"{texto}/mes"
                    
            # Buscar /mes en el siguiente span
            next_sibling = span.find_next_sibling()
            if next_sibling and "/mes" in next_sibling.get_text(strip=True):
                return f"{texto}/mes"
                
            # Si no encuentra /mes, devolver el precio simple
            return texto
    
    return ""

def extraer_vendedor(soup):
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "facebook.com/profile.php?id=" in href:
            link_v   = href.split("?")[0]
            strong   = a.find("strong")
            vendedor = strong.get_text(strip=True) if strong else ""
            return vendedor, link_v
    return "", ""

def guardar_archivos(html, datos, ciudad, pid, carpeta, date_str):
    """
    Guarda los archivos HTML, JSON y la imagen en la carpeta diaria
    """
    base = f"{ciudad}-{date_str}-{pid}"
    ruta_html = os.path.join(carpeta, base + ".html")
    ruta_json = os.path.join(carpeta, base + ".json")
    
    # Guardar HTML para depuración
    with open(ruta_html, "w", encoding="utf-8") as f:
        f.write(html)
    
    # Guardar JSON con los datos
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    
    return ruta_html, ruta_json

def descargar_imagen_por_playwright(page, ciudad, pid, carpeta, date_str):
    """
    Descarga la imagen principal de la propiedad
    """
    try:
        src = page.locator('img[alt^="Foto de"]').first.get_attribute('src')
    except:
        try:
            src = page.locator('img').first.get_attribute('src')
        except:
            return {
                "nombre_archivo": "",
                "ruta_absoluta": "",
                "ruta_relativa": ""
            }
            
    if not src or not src.startswith("http"):
        return {
            "nombre_archivo": "",
            "ruta_absoluta": "",
            "ruta_relativa": ""
        }
        
    filename = f"{ciudad}-{date_str}-{pid}.jpg"
    path_img = os.path.join(carpeta, filename)
    
    try:
        resp = requests.get(src, timeout=10)
        if resp.status_code == 200:
            with open(path_img, "wb") as f:
                f.write(resp.content)
            
            # Construir rutas para fácil acceso
            ruta_absoluta = os.path.abspath(path_img)
            # Construir ruta relativa desde la raíz del proyecto
            ruta_relativa = os.path.relpath(path_img, CARPETA_RESULTADOS).replace("\\", "/")
            
            return {
                "nombre_archivo": filename,
                "ruta_absoluta": ruta_absoluta,
                "ruta_relativa": ruta_relativa
            }
    except:
        pass
    
    return {
        "nombre_archivo": "",
        "ruta_absoluta": "",
        "ruta_relativa": ""
    }

def extraer_ubicacion_desde_dom(soup):
    """
    Extrae la ubicación desde el DOM, buscando en múltiples lugares y formatos
    """
    ubicacion = {
        "direccion_completa": "",
        "ciudad": "",
        "estado": "",
        "texto_original": ""
    }
    
    ciudades_conocidas = ["cuernavaca", "jiutepec", "temixco", "zapata", "yautepec", "tres de mayo", "burgos"]
    
    try:
        # Método 1: Buscar en elementos con atributos específicos de ubicación
        for elemento in soup.find_all(['span', 'div', 'a']):
            if elemento.get('aria-label') and 'ubicación' in elemento.get('aria-label').lower():
                texto = elemento.get_text(strip=True)
                if texto and any(ciudad in texto.lower() for ciudad in ciudades_conocidas):
                    ubicacion["texto_original"] = texto
                    ubicacion["direccion_completa"] = texto
                    break

        # Método 2: Buscar en la estructura de metadatos
        meta_location = soup.find('meta', {'property': 'og:locality'}) or soup.find('meta', {'property': 'place:location:locality'})
        if meta_location and meta_location.get('content'):
            texto = meta_location.get('content')
            if any(ciudad in texto.lower() for ciudad in ciudades_conocidas):
                ubicacion["texto_original"] = texto
                ubicacion["direccion_completa"] = texto

        # Método 3: Buscar en elementos cercanos al precio
        precio_elemento = None
        for elemento in soup.find_all(['span', 'div']):
            if elemento.get_text(strip=True).startswith('$'):
                precio_elemento = elemento
                break
        
        if precio_elemento:
            # Buscar en los siguientes 3 elementos hermanos
            siguiente = precio_elemento.find_next_sibling()
            for _ in range(3):
                if siguiente:
                    texto = siguiente.get_text(strip=True)
                    if texto and any(ciudad in texto.lower() for ciudad in ciudades_conocidas):
                        ubicacion["texto_original"] = texto
                        ubicacion["direccion_completa"] = texto
                        break
                    siguiente = siguiente.find_next_sibling()

        # Método 4: Buscar en cualquier texto que contenga las ciudades conocidas
        if not ubicacion["direccion_completa"]:
            for elemento in soup.find_all(['span', 'div'], class_=True):
                texto = elemento.get_text(strip=True)
                if len(texto) < 100 and any(ciudad in texto.lower() for ciudad in ciudades_conocidas):
                    if not any(palabra in texto.lower() for palabra in ["descripción", "ver menos", "inbox", "info"]):
                        ubicacion["texto_original"] = texto
                        ubicacion["direccion_completa"] = texto
                        break

        # Procesar la ubicación encontrada
        if ubicacion["direccion_completa"]:
            texto = ubicacion["direccion_completa"].lower()
            
            # Extraer ciudad
            for ciudad in ciudades_conocidas:
                if ciudad in texto:
                    if ciudad == "zapata" and "emiliano zapata" in texto:
                        ubicacion["ciudad"] = "Emiliano Zapata"
                    elif ciudad == "tres de mayo":
                        ubicacion["ciudad"] = "Tres de Mayo"
                    else:
                        ubicacion["ciudad"] = ciudad.title()
                    break
            
            # Extraer estado
            if any(estado in texto for estado in ["mor", "mor.", "morelos"]):
                ubicacion["estado"] = "Morelos"

    except Exception as e:
        print(f"Error al extraer ubicación: {str(e)}")
    
    return ubicacion

def guardar_datos_propiedad(datos, ruta_base):
    """
    Guarda los datos de la propiedad en formato JSON
    """
    ruta_json = os.path.join(ruta_base, "data.json")
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

def detectar_tipo_operacion(texto, descripcion=None, precio_str=None, precio_num=None):
    """Detecta tipo de operación según criterios de Pablo - CORREGIDO"""
    
    # 1) Si precio tiene /mes → RENTA (sin restricciones)
    if precio_str and "/mes" in precio_str.lower():
        return "Renta"
    
    # 2) Buscar palabras clave de RENTA en texto y descripción
    txt_completo = " ".join([texto or "", descripcion or ""]).lower()
    palabras_renta = ["renta", "rentar", "alquiler", "alquilar", "/mes", "mensual", "se renta"]
    if any(palabra in txt_completo for palabra in palabras_renta):
        return "Renta"
    
    # 3) Si descripción menciona venta → VENTA
    palabras_venta = ["en venta", "venta", "vender", "vendo", "vende", "sale"]
    if any(palabra in txt_completo for palabra in palabras_venta):
        return "Venta"
        
    # 4) Sin datos contundentes - usar precio como última opción
    if precio_num:
        if precio_num >= 300000:  # >= $300,000 → VENTA
            return "Venta"
        elif precio_num <= 50000:  # <= $50,000 → probablemente RENTA
            return "Renta"
        else:  # Entre $50K y $300K → DESCONOCIDO
            return "Desconocido"
    
    return "Desconocido"  # Por defecto

def extraer_caracteristicas(texto):
    """
    Extrae características detalladas de la propiedad.
    """
    caracteristicas = {
        "recamaras": None,
        "banos": None,
        "medio_bano": None,
        "niveles": None,
        "estacionamientos": None,
        "superficie_m2": None,
        "construccion_m2": None,
        "edad": None,
        "recamara_planta_baja": False,
        "cisterna": False,
        "capacidad_cisterna": None
    }
    
    texto = texto.lower()
    
    # Patrones mejorados para recámaras
    patrones_recamaras = [
        r'(\d+)\s*(?:rec(?:amaras?|ámaras?)?|hab(?:itaciones?)?|dormitorios?|cuartos?|alcobas?)',
        r'(?:rec(?:amaras?|ámaras?)?|hab(?:itaciones?)?|dormitorios?)\s*(?::|con)?\s*(\d+)',
        r'(?:casa|depto|departamento)\s+(?:de|con)\s+(\d+)\s*(?:rec|hab)',
        r'(\d+)\s*(?:habitaciones?|cuartos?)\s+(?:para\s+)?dormir'
    ]
    
    # Patrones para baños
    patrones_banos = [
        r'(\d+(?:\.\d+)?)\s*(?:baños?|banos?|wc|sanitarios?)',
        r'(?:baños?|banos?|wc|sanitarios?)\s*(?:completos?|principales?)?\s*(?::|con)?\s*(\d+(?:\.\d+)?)',
        r'(\d+)\s*(?:baños?|banos?)\s+(?:completos?|principales?)',
        r'medio\s+baño',
        r'baño\s+completo'
    ]
    
    # Patrones para superficie
    patrones_superficie = [
        r'(?:superficie|terreno|lote)\s*(?:de|:)?\s*(\d+(?:\.\d+)?)\s*(?:m²|m2|metros?|mt2|mts2)',
        r'(\d+(?:\.\d+)?)\s*(?:m²|m2|metros?|mt2|mts2)\s*(?:de\s*terreno|superficie)',
        r'(\d+)\s*x\s*(\d+)\s*(?:m²|m2|metros?)?',
        r'(\d+)\s*por\s*(\d+)\s*(?:m²|m2|metros?)?'
    ]
    
    # Patrones para construcción
    patrones_construccion = [
        r'(?:construccion|construcción)\s*(?:de|:)?\s*(\d+(?:\.\d+)?)\s*(?:m²|m2|metros?|mt2|mts2)',
        r'(\d+(?:\.\d+)?)\s*(?:m²|m2|metros?|mt2|mts2)\s*(?:de\s*construccion|de\s*construcción)',
        r'area\s*construida\s*(?:de|:)?\s*(\d+(?:\.\d+)?)\s*(?:m²|m2|metros?)'
    ]
    
    # Patrones para estacionamientos
    patrones_estacionamiento = [
        r'(\d+)\s*(?:cajone?s?|lugares?|espacios?)\s*(?:de\s*)?(?:estacionamiento|auto|coche|carro)',
        r'(?:estacionamiento|cochera|garage)\s*(?:para|con|de)\s*(\d+)\s*(?:auto|carro|coche)',
        r'(\d+)\s*(?:autos?|carros?|coches?)\s*(?:en\s*)?(?:cochera|garage|estacionamiento)',
        r'(?:con|incluye)\s*(\d+)\s*(?:lugares?|cajone?s?)\s*(?:de\s*)?estacionamiento'
    ]
    
    # Buscar recámaras
    for patron in patrones_recamaras:
        if match := re.search(patron, texto):
            try:
                caracteristicas["recamaras"] = int(match.group(1))
                break
            except:
                continue
    
    # Buscar baños
    total_banos = 0
    medio_bano = False
    
    for patron in patrones_banos:
        if match := re.search(patron, texto):
            try:
                if 'medio' in match.group(0):
                    medio_bano = True
                else:
                    num = float(match.group(1))
                    if num.is_integer():
                        total_banos = int(num)
                    else:
                        total_banos = int(num)
                        medio_bano = True
                break
            except:
                continue
    
    if total_banos > 0:
        caracteristicas["banos"] = total_banos
    if medio_bano:
        caracteristicas["medio_bano"] = 1
    
    # Buscar superficie
    for patron in patrones_superficie:
        if match := re.search(patron, texto):
            try:
                if 'x' in patron or 'por' in patron:
                    largo = float(match.group(1))
                    ancho = float(match.group(2))
                    caracteristicas["superficie_m2"] = int(largo * ancho)
                else:
                    caracteristicas["superficie_m2"] = int(float(match.group(1)))
                break
            except:
                continue
    
    # Buscar construcción
    for patron in patrones_construccion:
        if match := re.search(patron, texto):
            try:
                caracteristicas["construccion_m2"] = int(float(match.group(1)))
                break
            except:
                continue
    
    # Buscar estacionamientos
    for patron in patrones_estacionamiento:
        if match := re.search(patron, texto):
            try:
                caracteristicas["estacionamientos"] = int(match.group(1))
                break
            except:
                continue
    
    # Detectar recámara en planta baja
    if re.search(r'rec[aá]mara\s+(?:en\s+)?(?:planta\s+)?baja|rec[aá]mara\s+principal\s+abajo', texto):
        caracteristicas["recamara_planta_baja"] = True
    
    # Detectar cisterna
    if 'cisterna' in texto:
        caracteristicas["cisterna"] = True
        # Buscar capacidad de cisterna
        if match := re.search(r'cisterna\s*(?:de|con)?\s*(\d+)\s*(?:m3|litros?|metros?3?)', texto):
            try:
                caracteristicas["capacidad_cisterna"] = int(match.group(1))
            except:
                pass
    
    return caracteristicas

def extraer_y_guardar_dom(page, ciudad, pid, carpeta, date_str):
    """Extrae y guarda el DOM completo de la página"""
    try:
        # Obtener el DOM usando evaluate
        dom = page.evaluate("""() => {
            return document.documentElement.outerHTML;
        }""")
        
        # Crear nombre de archivo para el DOM
        filename = f"{ciudad}-{date_str}-{pid}-dom.html"
        path_dom = os.path.join(carpeta, filename)
        
        # Guardar el DOM
        with open(path_dom, "w", encoding="utf-8") as f:
            f.write(dom)
            
        return filename
    except Exception as e:
        print(f"Error al extraer DOM para {pid}: {e}")
        return ""

# ── Flujo principal ───────────────────────────────────────────────────
def main():
    # 1) Maestro previo
    data_master = {}
    if os.path.exists(CARPETA_REPO_MASTER):
        with open(CARPETA_REPO_MASTER, "r", encoding="utf-8") as f:
            data_master = json.load(f)

    # 2) Carga y normaliza enlaces desde archivo UNIFICADO
    # Guardamos también la lista original sin normalizar para poder re-escribirla si eliminamos entradas
    raw_links: list = []
    links      : list = []

    if os.path.exists(CARPETA_LINKS):
        with open(CARPETA_LINKS, "r", encoding="utf-8") as f:
            raw_links = json.load(f)

            for item in raw_links:
                if isinstance(item, str):
                    # Link simple como string
                    href = BASE_URL + item if item.startswith("/") else item
                    ciudad = "cuernavaca"
                    tipo_esperado = "Venta"  # Por defecto
                elif isinstance(item, dict):
                    # Link con metadatos
                    href = item.get("link", "")
                    href = BASE_URL + href if href.startswith("/") else href
                    ciudad = item.get("ciudad", "cuernavaca").lower()
                    tipo_esperado = item.get("tipo_esperado", "Venta")
                else:
                    continue
                pid = href.rstrip("/").split("/")[-1]
                links.append({
                    "link": href,
                    "id": pid,
                    "ciudad": ciudad,
                    "tipo_esperado": tipo_esperado
                })

    # 3) Determinar lista de propiedades a visitar
    if RECHECK_ALL:
        pending = links  # Re-visita absolutamente todos los links
        print("⚙️  RECHECK_ALL activado → Se revisarán todas las propiedades del repositorio de links")
    else:
        pending = [l for l in links if l["id"] not in data_master]

    # ── LÍMITE OPCIONAL PARA PRUEBAS RÁPIDAS ───────────────────────────────
    # Si se define la variable de entorno LIMIT_PENDIENTES (p.ej. 20),
    # se recortará la lista de pendientes a esa cantidad.
    try:
        max_p = int(os.getenv("LIMIT_PENDIENTES", "0"))
        if max_p > 0:
            pending = pending[:max_p]
            print(f"⚙️  MODO MUESTRA ACTIVADO → Se procesarán solo {len(pending)} propiedades (LIMIT_PENDIENTES={max_p})")
    except ValueError:
        pass

    # ── PRINT RESUMEN ANTES DE EMPEZAR ──
    total = len(links)
    total_venta = len([l for l in links if l["tipo_esperado"] == "Venta"])
    total_renta = len([l for l in links if l["tipo_esperado"] == "Renta"])
    falta = len(pending)
    falta_venta = len([p for p in pending if p["tipo_esperado"] == "Venta"])
    falta_renta = len([p for p in pending if p["tipo_esperado"] == "Renta"])
    
    print(f"\n=== RESUMEN DE PROPIEDADES (UNIFICADO) ===")
    print(f"Total en repositorio: {total}")
    print(f"- Propiedades en venta: {total_venta}")
    print(f"- Propiedades en renta: {total_renta}")
    print(f"\nPendientes de procesar: {falta}")
    print(f"- Ventas pendientes: {falta_venta}")
    print(f"- Rentas pendientes: {falta_renta}")
    print("=" * 30 + "\n")

    # 4) Carpeta diaria
    date_str = datetime.now().strftime("%Y-%m-%d")
    carpeta  = os.path.join(CARPETA_RESULTADOS, date_str)
    os.makedirs(carpeta, exist_ok=True)

    # 5) Lanzar navegador y barra de progreso
    pbar = ProgressBar(falta, desc="Extrayendo propiedades", unit="propiedad")
    ok = err = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=ESTADO_FB)
        page    = context.new_page()

        # Conjunto auxiliar para registrar IDs a eliminar si la publicación ya no existe
        ids_no_disponibles = set()

        for item in pending:
            pid    = item["id"]
            url    = item["link"]
            ciudad = item["ciudad"]
            tipo_esperado = item["tipo_esperado"]  # Tipo esperado del link
            t0     = time.time()
            try:
                page.goto(url, timeout=60000)
                page.wait_for_timeout(3000)
                # expandir "Ver más"
                try:
                    vm = page.locator("text=Ver más").first
                    if vm.is_visible():
                        vm.click(); page.wait_for_timeout(1000)
                except:
                    pass
                
                html = page.content()
                # ── DETECCIÓN DE PUBLICACIÓN NO DISPONIBLE ───────────────────────
                texto_baja = [
                    "listing isn",  # "listing isn't available"
                    "no longer available",
                    "contenido no disponible",
                    "contenido no está disponible",
                    "content isn't available",
                    "this content isn't available"
                ]
                if any(frase in html.lower() for frase in texto_baja):
                    print(f"ℹ️  Publicación {pid} ya no está disponible.")

                    # Si se pide eliminar, marcamos para depuración ulterior
                    if REMOVE_NOT_AVAILABLE:
                        ids_no_disponibles.add(pid)
                        # Eliminar inmediatamente del maestro si ya existía
                        if pid in data_master:
                            data_master.pop(pid, None)

                    err += 1
                    pbar.update(1, ok=ok, err=err, last_time=time.time()-t0)
                    continue
                
                soup = BeautifulSoup(html, "html.parser")
                
                titulo      = soup.find("h1").get_text(strip=True) if soup.find("h1") else ""
                descripcion = extraer_descripcion_estable(soup)
                precio_str  = extraer_precio_mejorado(soup)  # ✅ Función mejorada que preserva /mes
                precio_num  = procesar_numero_mexicano(precio_str) if precio_str else None
                vendedor, link_v = extraer_vendedor(soup)
                img_portada = descargar_imagen_por_playwright(page, ciudad, pid, carpeta, date_str)
                
                # Detectar tipo de operación con más contexto
                tipo_detectado = detectar_tipo_operacion(titulo, descripcion, precio_str, precio_num)
                
                # Usar tipo esperado como principal, detectado como validación
                tipo_final = tipo_esperado
                confianza_tipo = "alta" if tipo_detectado == tipo_esperado else "baja"
                
                # Validar precio según tipo de operación
                es_precio_valido, confianza_precio, mensaje_precio = validar_precio(precio_num, tipo_final)
                
                ubicacion   = extraer_ubicacion_desde_dom(soup)
                caracteristicas = extraer_caracteristicas(descripcion)
                
                # ── Mejora: usar extracción precisa vía JSON "pin" ──
                addr_precisa = extract_address_from_html(html)
                if addr_precisa:
                    ubicacion["direccion_completa"] = addr_precisa
                    low = addr_precisa.lower()
                    # Si aún no hay ciudad, inferirla
                    if not ubicacion.get("ciudad"):
                        for ciudad_key in ["cuernavaca", "jiutepec", "temixco", "zapata", "yautepec", "tres de mayo", "burgos"]:
                            if ciudad_key in low:
                                ubicacion["ciudad"] = "Emiliano Zapata" if ciudad_key == "zapata" else ciudad_key.title()
                                break
                    # Si aún no hay estado, inferir Morelos
                    if not ubicacion.get("estado") and any(x in low for x in ["mor", "mor.", "morelos"]):
                        ubicacion["estado"] = "Morelos"
                
                datos = {
                    "id": pid,
                    "link": url,
                    "titulo": titulo,
                    "precio": {
                        "texto": precio_str,
                        "valor": precio_num,
                        "es_valido": es_precio_valido,
                        "confianza": confianza_precio,
                        "mensaje": mensaje_precio
                    },
                    "ciudad": ciudad,
                    "vendedor": vendedor,
                    "link_vendedor": link_v,
                    "descripcion": descripcion,
                    "imagen_portada": img_portada,
                    "tipo_operacion": {
                        "tipo": tipo_final,
                        "tipo_detectado": tipo_detectado,
                        "confianza": confianza_tipo
                    },
                    "ubicacion": ubicacion,
                    "caracteristicas": caracteristicas,
                    "fecha_extraccion": datetime.now().isoformat(),
                    "archivos": {
                        "html": f"{ciudad}-{date_str}-{pid}.html",
                        "json": f"{ciudad}-{date_str}-{pid}.json",
                        "imagen": img_portada["nombre_archivo"] if isinstance(img_portada, dict) else img_portada
                    }
                }
                
                # Guardar archivos
                ruta_html, ruta_json = guardar_archivos(html, datos, ciudad, pid, carpeta, date_str)
                
                # Actualizar repositorio maestro
                data_master[pid] = datos
                with open(CARPETA_REPO_MASTER, "w", encoding="utf-8") as mf:
                    json.dump(data_master, mf, ensure_ascii=False, indent=2)
                ok += 1
                
            except Exception as e:
                err += 1
                print(f"❌ Error en {pid}: {e}")
            finally:
                pbar.update(1, ok=ok, err=err, last_time=time.time()-t0)

        pbar.close()
        page.close()
        browser.close()

    # ── Limpieza final de links no disponibles ──────────────────────────
    if REMOVE_NOT_AVAILABLE and ids_no_disponibles:
        print(f"🗑️  Eliminando {len(ids_no_disponibles)} publicaciones no disponibles del repositorio de links...")

        def _id_from_item(it):
            if isinstance(it, str):
                return (it.rstrip("/").split("/")[-1])
            elif isinstance(it, dict):
                href = it.get("link") or it.get("url") or it.get("href") or ""
                return (href.rstrip("/").split("/")[-1])
            else:
                return ""

        # --- Respaldo antes de sobrescribir ---
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.system(f"cp {CARPETA_LINKS} {CARPETA_LINKS}.backup_{timestamp}")
        os.system(f"cp {CARPETA_REPO_MASTER} {CARPETA_REPO_MASTER}.backup_{timestamp}")

        raw_links_filtrados = [it for it in raw_links if _id_from_item(it) not in ids_no_disponibles]

        # Sobrescribir archivo unificado
        with open(CARPETA_LINKS, "w", encoding="utf-8") as f:
            json.dump(raw_links_filtrados, f, ensure_ascii=False, indent=2)
        print("✅ Repositorio de links actualizado")

    # Imprimir resumen final
    print(f"\n=== RESUMEN FINAL ===")
    print(f"Total de propiedades procesadas: {ok + err}")
    print(f"- Exitosas: {ok}")
    print(f"- Con errores: {err}")
    print(f"\nTotal en repositorio maestro: {len(data_master)}")
    print("=" * 30 + "\n")
    
    # 🔔 Alerta de finalización (sonido + mensaje destacado)
    try:
        # Bell character para terminal compatible
        print("\a", end="")
    except:
        pass
    print("🔔  Extracción completada. Puedes revisar los resultados.")
    if REMOVE_NOT_AVAILABLE and ids_no_disponibles:
        print(f"🗑️  Se eliminaron {len(ids_no_disponibles)} IDs no disponibles del maestro y del archivo de links.")
    
    # ✅ PROCESAMIENTO AUTOMÁTICO INTEGRADO
    ejecutar_procesamiento_automatico(len(data_master))

def actualizar_html_con_conteo(conteo_propiedades):
    """Actualiza el HTML con el conteo real de propiedades"""
    try:
        html_file = "index_s3_latest.html"
        print(f"📝 Actualizando {html_file} con {conteo_propiedades} propiedades...")
        
        # Crear respaldo del HTML
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"ARCHIVOS_NO_PROYECTO/frontend_html_backup_{timestamp}.html"
        os.system(f"cp {html_file} {backup_file}")
        print(f"📁 Respaldo HTML creado: {backup_file}")
        
        # Leer HTML actual
        with open(html_file, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Actualizar todas las referencias al conteo
        # Buscar patrón: <option value="XXXX">Todas las propiedades</option>
        import re
        patron = r'<option value="\d+">Todas las propiedades</option>'
        nuevo_option = f'<option value="{conteo_propiedades}">Todas las propiedades</option>'
        contenido_actualizado = re.sub(patron, nuevo_option, contenido)
        
        # Buscar y actualizar lógica JavaScript también
        patron_js = r'if\s*\(\s*selectedValue\s*===?\s*["\']?\d+["\']?\s*\)'
        nuevo_js = f'if (selectedValue === "{conteo_propiedades}")'
        contenido_actualizado = re.sub(patron_js, nuevo_js, contenido_actualizado)
        
        # Guardar HTML actualizado
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(contenido_actualizado)
        
        print(f"✅ HTML actualizado correctamente con {conteo_propiedades} propiedades")
        return True
        
    except Exception as e:
        print(f"❌ Error actualizando HTML: {e}")
        return False

def subir_imagenes_automatico_s3():
    """Subir automáticamente todas las imágenes nuevas a S3"""
    print("📤 INICIANDO SUBIDA AUTOMÁTICA DE IMÁGENES A S3...")
    
    try:
        # Verificar que AWS CLI esté configurado
        result = subprocess.run(['aws', 'sts', 'get-caller-identity'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("⚠️  AWS CLI no configurado, saltando subida de imágenes")
            return False
        
        # Encontrar carpetas de fechas recientes (últimos 3 días)
        resultados_path = "resultados"
        if not os.path.exists(resultados_path):
            print("❌ Carpeta resultados/ no encontrada")
            return False
        
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        carpetas_fechas = []
        
        for item in os.listdir(resultados_path):
            carpeta_path = os.path.join(resultados_path, item)
            if os.path.isdir(carpeta_path) and item.startswith('2025-'):
                carpetas_fechas.append(item)
        
        if not carpetas_fechas:
            print("📷 No se encontraron carpetas de imágenes para subir")
            return True
        
        carpetas_fechas.sort(reverse=True)  # Más recientes primero
        carpetas_a_subir = carpetas_fechas[:3]  # Solo últimas 3 fechas
        
        print(f"📁 Carpetas a sincronizar: {carpetas_a_subir}")
        
        # Subir cada carpeta por separado
        total_subidas = 0
        for fecha in carpetas_a_subir:
            carpeta_local = os.path.join(resultados_path, fecha)
            
            # Contar imágenes en la carpeta
            imagenes_jpg = [f for f in os.listdir(carpeta_local) if f.endswith('.jpg')]
            if not imagenes_jpg:
                continue
                
            print(f"📤 Subiendo {len(imagenes_jpg)} imágenes de {fecha}...")
            
            # Comando AWS S3 sync optimizado
            cmd = [
                'aws', 's3', 'sync', 
                carpeta_local,
                f's3://todaslascasas-imagenes/{fecha}/',
                '--include', '*.jpg',
                '--exclude', '*',
                '--only-show-errors'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                total_subidas += len(imagenes_jpg)
                print(f"✅ {fecha}: {len(imagenes_jpg)} imágenes subidas")
            else:
                print(f"❌ Error subiendo {fecha}: {result.stderr}")
        
        if total_subidas > 0:
            print(f"🎉 SUBIDA COMPLETADA: {total_subidas} imágenes sincronizadas con S3")
            
            # Verificar algunas URLs de ejemplo
            ejemplo_carpeta = carpetas_a_subir[0] if carpetas_a_subir else None
            if ejemplo_carpeta:
                ejemplo_carpeta_path = os.path.join(resultados_path, ejemplo_carpeta)
                imagenes_ejemplo = [f for f in os.listdir(ejemplo_carpeta_path) if f.endswith('.jpg')][:2]
                
                print(f"🔗 URLs de ejemplo:")
                for img in imagenes_ejemplo:
                    url_ejemplo = f"https://todaslascasas-imagenes.s3.amazonaws.com/{ejemplo_carpeta}/{img}"
                    print(f"   {url_ejemplo}")
        
        return True
        
    except FileNotFoundError:
        print("❌ AWS CLI no está instalado o no está en el PATH")
        return False
    except Exception as e:
        print(f"❌ Error en subida automática de imágenes: {e}")
        return False

def ejecutar_procesamiento_automatico(conteo_propiedades):
    # DRY_RUN: si la variable de entorno DRY_RUN está activada (1/true/yes) se omite todo el
    # procesamiento posterior que toca la base PostgreSQL, sube imágenes o modifica index.html.
    if os.getenv('DRY_RUN', '0').lower() not in ('0', '', 'false', 'no'):
        print('\n⚙️  DRY_RUN activo → Se omite procesamiento automático (DB/S3/HTML).')
        return True
    """Ejecutar todo el procesamiento automático después de extracción"""
    print("\n" + "="*60)
    print("🤖 INICIANDO PROCESAMIENTO AUTOMÁTICO COMPLETO")
    print("="*60)
    
    try:
        # 1. Ejecutar procesamiento de propiedades
        print("\n🔄 PASO 1: Procesando propiedades extraídas...")
        subprocess.run([sys.executable, "src/procesa_propiedad.py"], check=True)
        print("✅ Procesamiento de propiedades completado")
        
        # 2. Cargar a PostgreSQL
        print("\n🔄 PASO 2: Cargando propiedades a PostgreSQL...")
        result = subprocess.run([sys.executable, "CARGAR_TODAS_PROPIEDADES_FINAL.py"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Carga a PostgreSQL completada")
            # Mostrar últimas líneas del resultado
            if result.stdout:
                lineas = result.stdout.strip().split('\n')
                for linea in lineas[-3:]:
                    if linea.strip():
                        print(f"   {linea}")
        else:
            print(f"❌ Error en carga PostgreSQL: {result.stderr}")
            return False
        
        # 3. Subir imágenes a S3
        print("\n🔄 PASO 3: Subiendo imágenes a S3...")
        subida_exitosa = subir_imagenes_automatico_s3()
        if subida_exitosa:
            print("✅ Subida de imágenes completada")
        else:
            print("⚠️  Subida de imágenes no completada (continuando)")
        
        # 4. Actualizar HTML
        print("\n🔄 PASO 4: Actualizando HTML con conteo real...")
        actualizar_html_con_conteo(conteo_propiedades)
        print("✅ HTML actualizado")
        
        # 5. Verificar PostgreSQL
        print("\n🔄 PASO 5: Verificando estado final...")
        verificar_postgresql()
        
        print("\n" + "="*60)
        print("🎉 PROCESAMIENTO AUTOMÁTICO COMPLETADO EXITOSAMENTE")
        print("🌐 Sitio web: https://todaslascasas.mx")
        print("🔗 API: https://w9k13jp1xb.execute-api.us-east-1.amazonaws.com/dev")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error en procesamiento automático: {e}")
        return False

def verificar_postgresql():
    """Verifica que PostgreSQL tenga los datos correctos"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="todaslascasas-postgres.cqpcyeqa0uqj.us-east-1.rds.amazonaws.com",
            database="propiedades_db", 
            user="pabloravel",
            password="Todaslascasas2025",
            port="5432"
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM propiedades;")
        count = cursor.fetchone()[0]
        
        print(f"📊 PostgreSQL: {count} propiedades verificadas")
        
        cursor.close()
        conn.close()
        
        return count
        
    except Exception as e:
        print(f"⚠️  No se pudo verificar PostgreSQL: {e}")
        return 0

if __name__ == '__main__':
    main()