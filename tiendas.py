# -*- coding: utf-8 -*-
"""
Tiendas de diseno vintage a precio fijo: Pamono y 1stDibs.
(The Oblist es Shopify y va por shopify.py.)

Revisado el 2026-10-06, antes de escribir una linea:

  Pamono   robots.txt permite las categorias; prohibe /catalog/, /checkout/,
           /customer/, /wishlist/ y poco mas. Sus condiciones no dicen nada de
           lectura automatizada. Se leen las categorias ordenadas por precio
           ascendente y se para al pasar el tope: casi nunca hace falta pasar
           de la segunda pagina.
  1stDibs  robots.txt prohibe /search/, /item/, cualquier ?q= y la paginacion
           de /buy/. Las categorias (/furniture/storage-case-pieces/dressers/)
           y el filtro ?price= estan permitidos. Cada pagina trae un bloque
           JSON-LD con nombre, precio, foto, categoria y ano: no hace falta
           abrir las fichas. Su acuerdo de usuario pide cumplir "accepted
           Internet protocol", que es exactamente robots.txt.

Las dos con el mismo trato que las casas de subastas: sin cuenta, una peticion
cada 3 s, User-Agent con contacto real y parada total ante un 403.

Uso:
    .venv/bin/python tiendas.py             las dos
    .venv/bin/python tiendas.py pamono      una
"""
import html
import json
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from etsy import A_EUR, medidas_de_texto
from scraper import DIR_DATOS, ParadaTotal, guardar, traer

TOPE_EUR = 900          # por encima no se guarda: la pagina filtra hasta aqui


def ahora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def limpio(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def lote(casa, nombre, titulo, url, precio, **extra):
    base = {
        "casa": casa, "casa_nombre": nombre, "lote": None,
        "titulo": titulo[:300], "texto": titulo, "salida": precio,
        "imagen": None, "url": url, "origen": url, "no_vendido": False,
        "lado_mayor_cm": 0, "ubicacion": None, "precio_fijo": True,
        "historico": False, "visto": ahora(),
    }
    base.update(extra)
    return base


def medidas_txt(m):
    """{'ancho':76,'fondo':42,'alto':106} -> ('76 x 42 x 106 cm', 106)"""
    vals = [v for v in (m.get("ancho"), m.get("fondo"), m.get("alto")) if v]
    if len(vals) < 2:
        return "", 0
    return " x ".join(str(round(v)) for v in vals) + " cm", max(vals)


# ===========================================================================
# PAMONO
# ===========================================================================
PAMONO = "https://www.pamono.es"
# Las categorias "base" son vintage y antiguedades; las "contemporaneo-*" se
# dejan fuera a proposito.
# Muebles de guardar: se leen mas paginas y sus fichas se abren primero
PAMONO_ALMACENAJE = ["comodas-cajoneras", "comodas-mid-century", "aparadores",
                     "aparadores-buffets", "credenzas", "armarios", "alacenas-armarios",
                     "barras-armarios-de-bar-1"]
PAMONO_CATEGORIAS = PAMONO_ALMACENAJE + [
    "mesitas-noche", "librerias-estanterias", "escritorios",
    "lamparas-mesa", "lamparas-pared-apliques", "lamparas-pie",
    "sillas-auxiliares-sillas-comedor", "sillas-escritorio-oficina",
    "objetos-escultoricos-de-pared",
]
# Se abre la ficha (para sacar medidas, disenador, ano) solo de estas, que es
# donde las medidas deciden: el encargo de la cajonera.
PAMONO_CON_FICHA = set(PAMONO_ALMACENAJE) | {"mesitas-noche", "librerias-estanterias", "escritorios"}
CACHE_FICHAS = os.path.join(DIR_DATOS, "pamono_fichas.json")

RE_CARD = re.compile(r'<article class="product-card"(.*?)</article>', re.S)
RE_HREF = re.compile(r'class="link-wrapper" href="([^"]+)" title="([^"]*)"')
RE_PRECIO = re.compile(r'itemprop="price" content="(\d+(?:\.\d+)?)"')
RE_ANTES = re.compile(r'itemprop="old-price" content="(\d+(?:\.\d+)?)"')
RE_IMG = re.compile(r'data-lazy="([^"]+)"')
RE_FILA = re.compile(r'<th scope="row">\s*(.*?)\s*</th>\s*<td>(.*?)</td>', re.S)


def pamono_categoria(cat, tope=TOPE_EUR, max_paginas=4):
    out, vistos = [], set()
    for p in range(1, max_paginas + 1):
        url = f"{PAMONO}/{cat}?order=price&dir=asc" + (f"&p={p}" if p > 1 else "")
        h = traer(url)
        if not h:
            break
        tarjetas = RE_CARD.findall(h)
        nuevos, mas_caro = 0, 0.0
        for c in tarjetas:
            mh, mp = RE_HREF.search(c), RE_PRECIO.search(c)
            if not mh or not mp:
                continue
            href, titulo = mh.group(1), html.unescape(mh.group(2))
            precio = float(mp.group(1))
            mas_caro = max(mas_caro, precio)
            # precio > tope: fuera. Menos de 20 EUR: Pamono pone 2 o 3 EUR a lo que
            # no tiene precio publico, no es una ganga
            if href in vistos or precio > tope or precio < 20:
                continue
            vistos.add(href)
            nuevos += 1
            ma, mi = RE_ANTES.search(c), RE_IMG.search(c)
            # el listado enlaza el recorte a 300 px (/p/m/); el mismo a 440 es /p/z/
            img = mi.group(1).replace("/p/m/", "/p/z/") if mi else None
            l = lote("pamono", "Pamono", titulo, href, precio, imagen=img, categoria=cat)
            if ma and float(ma.group(1)) > precio:
                # la propia tienda lo ha rebajado: es la senal de oportunidad
                l["precio_anterior"] = float(ma.group(1))
            out.append(l)
        # orden ascendente: si esta pagina ya pasa del tope, la siguiente tambien.
        # Y Magento repite la ultima pagina si se pide una de mas.
        if not nuevos or mas_caro > tope:
            break
    print(f"  {len(out):4d}  {cat}")
    return out


def pamono_filas(h):
    """
    La tabla de datos de la ficha, fila a fila. Con BeautifulSoup y no con una
    regex: la fila "Color" trae otro formato y la regex se comia la fila
    siguiente ("Ancho"), asi que casi todas las piezas perdian una medida.
    """
    from bs4 import BeautifulSoup
    filas = {}
    for tr in BeautifulSoup(h, "lxml").select("tr"):
        th, td = tr.find("th"), tr.find("td")
        if not th or not td:
            continue
        clave = limpio(th.get_text(" "))
        # cada medida sale dos veces (oculta para schema.org y visible): la visible
        spans = [x for x in td.find_all("span", recursive=False) if "schema-only" not in (x.get("class") or [])]
        valor = limpio(spans[0].get_text(" ")) if spans else limpio(td.get_text(" "))
        if clave and clave not in filas:
            filas[clave] = valor
    return filas


def pamono_ficha(url):
    h = traer(url)
    if not h:
        return {}
    filas = pamono_filas(h)
    m = {}
    for clave, eje in (("Ancho", "ancho"), ("Profundidad", "fondo"),
                       ("Altura", "alto"), ("Diámetro", "ancho")):
        n = re.search(r"(\d+(?:[.,]\d+)?)\s*cm", filas.get(clave, ""))
        if n and eje not in m:
            m[eje] = float(n.group(1).replace(",", "."))
    desc = ""
    md = re.search(r'itemprop="description"[^>]*>(.*?)</div>', h, re.S)
    if md:
        desc = limpio(md.group(1))[:900]
    # primera foto de verdad (no el recorte): /p/z/ la sirve a 1.600 px
    foto = None
    mo = re.search(r'property="og:image" content="([^"]+)"', h) or re.search(r'og:image" content="([^"]+)"', h)
    if mo:
        foto = re.sub(r"/p/[a-z]/", "/p/z/", mo.group(1))
    return {"medidas": m, "filas": filas, "desc": desc, "foto": foto, "v": 3}


def pamono(tope=TOPE_EUR, max_fichas=200):
    print("\n=== Pamono (categorias, por precio ascendente) ===")
    lotes = []
    for cat in PAMONO_CATEGORIAS:
        lotes += pamono_categoria(cat, tope, max_paginas=10 if cat in PAMONO_ALMACENAJE else 4)
    # fichas: se cachean por URL, asi cada dia solo se abren las nuevas
    cache = json.load(open(CACHE_FICHAS, encoding="utf-8")) if os.path.exists(CACHE_FICHAS) else {}
    cache = {u: v for u, v in cache.items() if v.get("v") == 3}
    pendientes = [l for l in lotes if l["categoria"] in PAMONO_CON_FICHA and l["url"] not in cache]
    pendientes.sort(key=lambda l: l["categoria"] not in PAMONO_ALMACENAJE)   # guardar, primero
    if pendientes:
        print(f"  abriendo {min(len(pendientes), max_fichas)} fichas nuevas de "
              f"{len(pendientes)} (medidas y disenador)")
    for l in pendientes[:max_fichas]:
        cache[l["url"]] = pamono_ficha(l["url"])
    with open(CACHE_FICHAS, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)
    for l in lotes:
        fi = cache.get(l["url"]) or {}
        txt, lado = medidas_txt(fi.get("medidas") or {})
        f = fi.get("filas") or {}
        datos = [f.get(k) for k in ("Diseñador", "Creador", "Fabricante", "Año",
                                    "Época del diseño", "Periodo de produccion", "Estilo",
                                    "Material", "Estado detallado", "País de fabricación")]
        # La descripcion en prosa no viene en el HTML (se carga al pulsar), y lo
        # que hay en su sitio es el rotulo "Diseno Vintage", que sumaba "diseno"
        # a todas las piezas. Lo que describe la pieza es la tabla de datos.
        l["texto"] = " . ".join(x for x in [l["titulo"], txt, *datos] if x)[:1500]
        l["lado_mayor_cm"] = lado
        if fi.get("foto"):
            l["imagen_grande"] = fi["foto"]
        # el pais desde el que se envia: cuenta para el transporte y la aduana
        if f.get("Envía desde"):
            l["ubicacion"] = f["Envía desde"]
    print(f"  TOTAL Pamono: {len(lotes)} piezas hasta {tope} EUR")
    return lotes


# ===========================================================================
# 1STDIBS
# ===========================================================================
DIBS = "https://www.1stdibs.com"
DIBS_ALMACENAJE = [
    "furniture/storage-case-pieces/cabinets",
    "furniture/storage-case-pieces/wardrobes-armoires",
    "furniture/storage-case-pieces/buffets",
    "furniture/storage-case-pieces/cupboards",
    "furniture/storage-case-pieces/vitrines",
    "furniture/storage-case-pieces/dry-bars",
    "furniture/storage-case-pieces/apothecary-cabinets",
]
DIBS_CATEGORIAS = DIBS_ALMACENAJE + [
    "furniture/storage-case-pieces/dressers",
    "furniture/storage-case-pieces/commodes-chests-of-drawers",
    "furniture/storage-case-pieces/sideboards",
    "furniture/storage-case-pieces/credenzas",
    "furniture/more-furniture-collectibles/bedroom-furniture/night-stands",
    "furniture/lighting/table-lamps",
    "furniture/lighting/floor-lamps",
    "furniture/lighting/sconces-wall-lights",
    "furniture/seating/dining-room-chairs",
    "furniture/seating/lounge-chairs",
    "furniture/decorative-objects/sculptures",
    "art/sculptures",
]
RE_LD = re.compile(r'<script data-react-helmet="true" type="application/ld\+json">(.*?)</script>', re.S)
RE_CANON = re.compile(r'rel="canonical" href="([^"]+)"')


def dibs_categoria(cat, tope_eur=TOPE_EUR, max_paginas=3):
    tope_usd = round(tope_eur / A_EUR["USD"])
    out = []
    for p in range(1, max_paginas + 1):
        url = f"{DIBS}/{cat}/?price=%5B0%20TO%20{tope_usd}%5D" + (f"&page={p}" if p > 1 else "")
        h = traer(url)
        if not h:
            break
        canon = RE_CANON.search(h)
        if p == 1 and canon and canon.group(1).rstrip("/") != f"{DIBS}/{cat}":
            # la categoria no existe y 1stDibs redirige a la madre: no la leo
            print(f"     -  {cat}: no existe (redirige a {canon.group(1)})")
            return []
        m = RE_LD.search(h)
        if not m:
            break
        try:
            bloque = json.loads(m.group(1))
            items = bloque[0]["mainEntity"]["offers"]["itemOffered"]
        except (ValueError, KeyError, IndexError, TypeError):
            break
        if not items:
            break
        for it in items:
            of = it.get("offers") or {}
            moneda = of.get("priceCurrency", "USD")
            try:
                precio = float(of.get("price"))
            except (TypeError, ValueError):
                continue
            eur = round(precio * A_EUR[moneda], 2) if moneda in A_EUR else None
            if "InStock" not in (of.get("availability") or "InStock"):
                continue
            titulo = html.unescape(it.get("name") or "")
            desc = html.unescape(it.get("description") or "")
            ano = str(it.get("productionDate") or "")
            med = medidas_de_texto(desc)
            txt, lado = medidas_txt(med)
            avisos = []
            if moneda != "EUR":
                avisos.append(f"precio en {moneda}; el valor en euros es aproximado")
            avisos.append("1stDibs: mira desde donde envia; si es fuera de la UE, aduana e IVA aparte")
            out.append(lote(
                "1stdibs", "1stDibs", titulo, it.get("url") or url, eur,
                texto=" . ".join(x for x in [titulo, txt, ano, it.get("category") or "", desc] if x)[:1500],
                imagen=(it.get("image") or "").split("?")[0] + "?width=768" if it.get("image") else None,
                imagen_grande=(it.get("image") or "").split("?")[0] + "?width=1600" if it.get("image") else None,
                precio_original=f"{precio:.2f} {moneda}",
                lado_mayor_cm=lado, avisos_fuente=avisos, categoria=cat,
                epoca_etsy=ano or None,
            ))
        if len(items) < 24:
            break
    print(f"  {len(out):4d}  {cat}")
    return out


def primerdibs(tope=TOPE_EUR):
    print("\n=== 1stDibs (categorias con filtro de precio) ===")
    lotes = []
    for cat in DIBS_CATEGORIAS:
        guardar_ = cat in DIBS_ALMACENAJE or "storage-case-pieces" in cat
        lotes += dibs_categoria(cat, tope, max_paginas=5 if guardar_ else 3)
    vistos, unicos = set(), []
    for l in lotes:
        if l["url"] not in vistos:
            vistos.add(l["url"])
            unicos.append(l)
    print(f"  TOTAL 1stDibs: {len(unicos)} piezas hasta {tope} EUR")
    return unicos


FUENTES = {"pamono": pamono, "1stdibs": primerdibs}


if __name__ == "__main__":
    elegidas = [a for a in sys.argv[1:] if a in FUENTES] or list(FUENTES)
    todo = []
    for f in elegidas:
        try:
            todo += FUENTES[f]()
        except ParadaTotal as e:
            print(f"\n!! PARADA TOTAL en {f}: {e}\n   No reintentes en bucle.")
        except Exception as e:   # noqa: BLE001 - una fuente rota no tumba la otra
            print(f"\n!! fallo en {f}: {type(e).__name__}: {e}")
    if todo:
        nuevos, total = guardar(todo)
        print(f"\nGuardados: {nuevos} nuevos, {total} en total.")
