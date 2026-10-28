# -*- coding: utf-8 -*-
"""
Scraper de las casas de Madrid que corren sobre el CMS de Labelgrup.

Reglas de conducta, de la investigacion legal:
  - SIN SESION. Nunca con cookies de login. El raspado ocurre como navegacion
    publica anonima, no bajo el contrato de usuario. La cuenta es solo para pujar
    a mano desde el navegador.
  - User-Agent identificable con contacto, no disfrazado de Chrome.
  - 1 peticion cada 3 segundos, un hilo, una pasada al dia.
  - Parada total ante 403. Backoff ante 429/503.
  - NO se descargan las fotos de los lotes: se guarda la URL y se enlaza.
  - Los robots.txt de las cinco casas dicen "Disallow:" (todo permitido),
    comprobado el 2026-09-30. Si eso cambia, este scraper debe parar.
"""
import json
import os
import re
import time
import urllib.parse
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from casas import CASAS

from config import UA  # correo en config_local.py, fuera del repo
PAUSA = 3.0
DIR_DATOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos")

_ultima = [0.0]
HISTORICOS = set()   # catalogos que vienen de /subastas-historicas/


class ParadaTotal(Exception):
    """403: el servidor nos ha cerrado la puerta. Se para y se avisa."""


def _esperar():
    delta = time.time() - _ultima[0]
    if delta < PAUSA:
        time.sleep(PAUSA - delta)
    _ultima[0] = time.time()


RE_BR_PEGADO = re.compile(r"([a-z0-9]+)br([a-z]{3,})")


def despegar_br(titulo, texto=""):
    """
    Segre y Sala Retiro hacen el slug de la URL con el HTML del titulo, y cada
    <br> queda como "br" pegado: "para biokbrcomoda rectangular". Asi "comoda"
    no se encuentra como palabra. Se separa solo si la palabra pegada NO existe
    en el texto del lote, para no romper "sobre", "obra" o "abrir".
    """
    import unicodedata
    plano = unicodedata.normalize("NFD", (texto or "").lower())
    plano = "".join(c for c in plano if unicodedata.category(c) != "Mn")

    def _uno(m):
        return m.group(0) if m.group(0) in plano else f"{m.group(1)} {m.group(2)}"
    return RE_BR_PEGADO.sub(_uno, titulo or "")


def traer(url, intentos=3):
    """GET educado. Devuelve el HTML o None."""
    for n in range(intentos):
        _esperar()
        try:
            r = requests.get(url, headers={"User-Agent": UA,
                                           "Accept-Language": "es-ES,es;q=0.9"},
                             timeout=30)
        except requests.RequestException as e:
            print(f"    red: {e}")
            time.sleep(5 * (n + 1))
            continue
        if r.status_code == 403:
            raise ParadaTotal(f"403 en {url}. Parar y revisar antes de reintentar.")
        if r.status_code in (429, 503):
            espera = 30 * (n + 1)
            print(f"    {r.status_code}, esperando {espera}s")
            time.sleep(espera)
            continue
        if r.status_code == 200:
            return r.text
        print(f"    HTTP {r.status_code} en {url}")
        return None
    return None


# ---------------------------------------------------------------------------
# Parseo
# ---------------------------------------------------------------------------
RE_PRECIO = re.compile(r"([\d.]+)(?:,(\d{2}))?\s*€")
RE_MEDIDAS = re.compile(
    r"(\d{1,4}(?:[.,]\d+)?)\s*(?:x|X|×)\s*(\d{1,4}(?:[.,]\d+)?)"
    r"(?:\s*(?:x|X|×)\s*(\d{1,4}(?:[.,]\d+)?))?\s*(cm|mm|m\b)?", re.I)
RE_LOTE = re.compile(r"(?:LOTE|Lote|REFERENCIA)\s*:?\s*(\d+)")


def _num(txt):
    m = RE_PRECIO.search(txt or "")
    if not m:
        return None
    entero = m.group(1).replace(".", "")
    dec = m.group(2) or "0"
    try:
        return float(f"{entero}.{dec}")
    except ValueError:
        return None


def medidas_cm(texto):
    """Devuelve el lado mayor en cm, para el filtro de gran formato."""
    mejor = 0.0
    for m in RE_MEDIDAS.finditer(texto or ""):
        unidad = (m.group(4) or "cm").lower()
        vals = []
        for g in (m.group(1), m.group(2), m.group(3)):
            if not g:
                continue
            try:
                vals.append(float(g.replace(",", ".")))
            except ValueError:
                pass
        if not vals:
            continue
        factor = {"mm": 0.1, "m": 100.0}.get(unidad, 1.0)
        mejor = max(mejor, max(vals) * factor)
    return mejor if 3 < mejor < 2000 else 0.0


def extraer_lotes(html, casa_id, url_origen):
    """
    Extrae lotes de una pagina de listado de Labelgrup.
    El marcado varia entre casas, asi que se trabaja sobre bloques de texto
    y no sobre un selector unico. Deliberado: la investigacion avisa de que
    'NO asumas un solo selector para las cinco casas'.
    """
    soup = BeautifulSoup(html, "lxml")
    for basura in soup(["script", "style", "noscript"]):
        basura.decompose()

    base = CASAS[casa_id]["base"]
    lotes, vistos = [], set()

    # Cada lote suele colgar de un enlace a /es/subasta-lote/ o /es/lote/
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not re.search(r"/(subasta-lote|lote|producto|product)/", href):
            continue
        url = urllib.parse.urljoin(base, href)
        if url in vistos:
            continue

        # El contenedor del lote: subimos hasta encontrar texto con precio
        cont, texto = a, ""
        for _ in range(4):
            if cont is None:
                break
            texto = cont.get_text(" ", strip=True)
            if "€" in texto and len(texto) > 40:
                break
            cont = cont.parent
        if "€" not in texto:
            continue

        vistos.add(url)
        precio = _num(texto)
        if precio is None:
            continue

        m_lote = RE_LOTE.search(texto)
        titulo = a.get_text(" ", strip=True)
        if len(titulo) < 6 or titulo.upper().startswith(("NO DISPONIBLE", "NO VENDIDO")):
            img = a.find("img")
            alt = (img.get("alt") or "").strip() if img else ""
            titulo = alt if len(alt) > 5 else titulo
        # el slug de la URL lleva el titulo y el numero de lote: /<n>-<ref>-<TITULO>
        partes = [p for p in urllib.parse.unquote(url.rstrip("/")).split("/") if p]
        ultimo = partes[-1] if partes else ""
        # Sala Retiro/Segre: .../<nlote>-<ref>-<TITULO>
        m_slug = re.match(r"(\d+)-(\d+)-(.+)", ultimo)
        bonito = ""
        if m_slug:
            if not m_lote:
                m_lote = m_slug
            bonito = m_slug.group(3)
        # Duran/Ansorena: .../subasta-lote/<TITULO>/<subasta>-<nlote>
        elif re.match(r"^\d+-\d+$", ultimo) and len(partes) >= 2:
            bonito = partes[-2]
            if not m_lote:
                m_lote = re.match(r"\d+-(\d+)", ultimo)
        bonito = re.sub(r"[-_]+", " ", bonito).strip()
        if len(bonito) > len(titulo):
            titulo = bonito
        # Duran mete basura de layout en el texto del ancla
        titulo = re.sub(r"\s*presencial\s+Lote\s*:?\s*\d*\s*", "", titulo).strip()
        titulo = re.sub(r"\s*Precio salida.*$", "", titulo).strip()
        titulo = re.sub(r"\s{2,}", " ", titulo)
        titulo = despegar_br(titulo, texto)

        img_url = None
        img = (cont or a).find("img") if cont else a.find("img")
        if img:
            img_url = img.get("data-src") or img.get("src")
            if img_url:
                img_url = urllib.parse.urljoin(base, img_url)

        vendido = bool(re.search(r"NO VENDIDO|NO DISPONIBLE|Vendido", texto, re.I))

        lotes.append({
            "casa": casa_id,
            "casa_nombre": CASAS[casa_id]["nombre"],
            "lote": m_lote.group(1) if m_lote else None,
            "titulo": titulo[:300],
            "texto": texto[:1500],
            "salida": precio,
            "imagen": img_url,
            "url": url,
            "origen": url_origen,
            "no_vendido": vendido,
            "lado_mayor_cm": medidas_cm(texto),
            "visto": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })
    return lotes


def paginar(url, max_paginas=12):
    """Devuelve (url, html) de ?page=1..N; el llamador corta cuando no hay nuevos."""
    for p in range(1, max_paginas + 1):
        sep = "&" if "?" in url else "?"
        u = url if p == 1 else f"{url}{sep}page={p}"
        html = traer(u)
        if not html:
            break
        yield u, html


RE_SUBASTA = re.compile(r"/es/subasta/[^\"'#?]+")


def subastas_en(html, base):
    """
    Una pagina de 'presenciales' lista subastas, no lotes. Hay que entrar en cada
    catalogo. Devuelve las URLs de catalogo encontradas.
    """
    urls = []
    for m in RE_SUBASTA.finditer(html or ""):
        u = urllib.parse.urljoin(base, m.group(0))
        if u not in urls:
            urls.append(u)
    return urls


def rastrear_duran(max_paginas=10):
    """Duran carga por AJAX con token CSRF. Navegacion publica, sin login."""
    import duran as mod
    casa = CASAS["duran"]
    print(f"\n=== {casa['nombre']} (via AJAX) ===")
    encontrados, vistas = [], set()
    for ruta in casa["listados"]:
        try:
            ses, token, _ = mod.sesion_con_token(ruta)
        except Exception as e:
            print(f"  no se pudo abrir {ruta}: {e}")
            continue
        print(f"  {ruta}")
        for p in range(1, max_paginas + 1):
            _esperar()
            try:
                r = mod.pedir_lotes(ses, token, ruta, p)
            except Exception as e:
                print(f"    page {p}: {e}")
                break
            if r.status_code != 200 or len(r.text) < 400:
                break
            lotes = [l for l in extraer_lotes(r.text, "duran", mod.BASE + ruta)
                     if l["url"] not in vistas]
            for l in lotes:
                vistas.add(l["url"])
            print(f"    page {p}: {len(lotes)} lotes")
            if not lotes:
                break
            encontrados += lotes
    print(f"  TOTAL {casa['nombre']}: {len(encontrados)}")
    return encontrados


def rastrear_casa(casa_id, max_paginas=8, con_historico=False):
    """
    Pasada normal = SOLO lo que esta a la venta.

    El archivo historico de Alcala son decenas de catalogos de 8 paginas a 3
    segundos por peticion: horas. Y no cambia. Se baja una vez con
    --historico y luego se deja en paz.
    """
    if casa_id == "duran":
        return rastrear_duran()
    casa = CASAS[casa_id]
    print(f"\n=== {casa['nombre']} ===")
    encontrados, urls_vistas = [], set()

    # 1) expandir listados de subastas a catalogos de lote
    rutas = [r for r in casa["listados"] if con_historico or "histor" not in r]
    for ruta in list(rutas):
        url = urllib.parse.urljoin(casa["base"], ruta)
        if "/subasta/" in url:
            continue
        html = traer(url)
        if not html:
            continue
        nuevas = [u for u in subastas_en(html, casa["base"])
                  if u not in [urllib.parse.urljoin(casa["base"], r) for r in rutas]]
        if nuevas:
            es_hist = "histor" in ruta
            print(f"  + {len(nuevas)} catalogos desde {ruta}"
                  + ("  (HISTORICO)" if es_hist else ""))
            for u in nuevas:
                HISTORICOS.add(u) if es_hist else None
            rutas += nuevas

    for ruta in rutas:
        url = urllib.parse.urljoin(casa["base"], ruta)
        print(f"  {url}")
        for u, html in paginar(url, max_paginas):
            lotes = [l for l in extraer_lotes(html, casa_id, u)
                     if l["url"] not in urls_vistas]
            es_hist = u.split("?")[0] in HISTORICOS
            for l in lotes:
                l["historico"] = es_hist
            for l in lotes:
                urls_vistas.add(l["url"])
            encontrados += lotes
            print(f"    {u.split('?')[-1][:24] or 'pag 1'}: {len(lotes)} lotes")
            if not lotes:
                break
    print(f"  TOTAL {casa['nombre']}: {len(encontrados)}")
    return encontrados


def guardar(lotes, nombre="lotes.json"):
    os.makedirs(DIR_DATOS, exist_ok=True)
    ruta = os.path.join(DIR_DATOS, nombre)
    previos = []
    if os.path.exists(ruta):
        try:
            previos = json.load(open(ruta, encoding="utf-8"))
        except Exception:
            # No pisar en silencio los unicos datos que no se regeneran
            # (primera_vez, historico_salida): apartar el archivo y avisar.
            roto = ruta + ".roto"
            os.replace(ruta, roto)
            print(f"  AVISO: {nombre} ilegible, apartado como {os.path.basename(roto)}; se empieza de cero")
            previos = []
    por_url = {l["url"]: l for l in previos}
    nuevos = 0
    for l in lotes:
        if l["url"] not in por_url:
            nuevos += 1
            l["primera_vez"] = l["visto"]
        else:
            l["primera_vez"] = por_url[l["url"]].get("primera_vez", l["visto"])
            # el histórico de precios de salida delata la resubasta con -40 %
            hist = por_url[l["url"]].get("historico_salida", [])
            ant = por_url[l["url"]].get("salida")
            if ant is not None and ant != l["salida"]:
                hist.append({"fecha": l["visto"], "de": ant, "a": l["salida"]})
            l["historico_salida"] = hist
        por_url[l["url"]] = l
    # Escritura atomica: si el proceso muere a mitad, lotes.json no queda a
    # medias. os.replace es atomico dentro del mismo directorio.
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(list(por_url.values()), f, ensure_ascii=False, indent=1)
    os.replace(tmp, ruta)
    return nuevos, len(por_url)
