# -*- coding: utf-8 -*-
"""
eBay, por su API oficial (Browse API), en el mercado espanol (EBAY_ES).

Credenciales en config_local.py (fuera del repo), del keyset de PRODUCCION:
    EBAY_CLIENT_ID     = "..."    App ID
    EBAY_CLIENT_SECRET = "..."    Cert ID
Con ellas se pide un token de aplicacion ("client credentials", sin entrar con
ninguna cuenta), que dura dos horas y se guarda en datos/ hasta que caduca.

Lo que obliga su API License Agreement (leido el 2026-10-13) y como se cumple:
  - "Displayed item listing information may not be more than six (6) hours
    older than information displayed on the eBay Site"
    -> datos/ebay.json se SOBRESCRIBE en cada pasada; vista.py no lo carga si
       tiene mas de 6 h y la pagina oculta los anuncios de eBay cuando pasan de
       6 h desde la consulta, ensenando siempre cuanto hace que se consultaron.
       La tarea programada repasa eBay cada pocas horas para que no caduque.
  - "Making limited intermediate copies ... must be deleted when they are no
    longer required" -> un archivo, la ultima pasada, nada mas.
  - "eBay Content in a Public Display may not be co-mingled or combined with
    non-eBay Content" -> la regla es para mostrar al publico. Caxi-Vaxi es una
    pagina privada (Diego y su pareja, con acceso por invitacion), asi que eBay
    va mezclado con lo demas. compartir.py, que publica con enlace abierto, lo
    sigue dejando fuera.
  - "You will not ... collect, store or share any eBay User' User IDs" -> no se
    guarda el vendedor ni ningun dato de personas. Es lo que se declara en la
    exencion "Not persisting eBay data" de las notificaciones de borrado.
  - prohibido usar sus datos para "suggest or model prices" -> eBay no entra en
    comparables.py ni en ningun calculo de precio de referencia.
  - "reasonable request volume" -> una pasada al dia, tope de 400 peticiones.

Uso:
    .venv/bin/python ebay.py                    busquedas del perfil, piezas en Espana
    .venv/bin/python ebay.py --ue               lo mismo, piezas en toda la UE
    .venv/bin/python ebay.py "comoda teca"      una busqueda suelta
    .venv/bin/python ebay.py --categorias aparador   ids de categoria de eBay.es
"""
import base64
import json
import os
import re
import sys
import time
import urllib.parse
import warnings
from datetime import datetime, timezone

warnings.simplefilter("ignore")
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from etsy import A_EUR
from scraper import DIR_DATOS
from tiendas import TOPE_EUR, lote, medidas_txt
from wallapop import medidas_libres, sin_etiquetas

API = "https://api.ebay.com"
TOKEN_URL = API + "/identity/v1/oauth2/token"
ALCANCE = "https://api.ebay.com/oauth/api_scope"
MERCADO = "EBAY_ES"
ARBOL_ES = "186"            # arbol de eBay.es; se confirma con la Taxonomy API
ARCHIVO = os.path.join(DIR_DATOS, "ebay.json")
CACHE_TOKEN = os.path.join(DIR_DATOS, "ebay_token.json")
MAX_HORAS = 6
PAUSA = 0.5
TOPE_PETICIONES = 400

# Categorias para acotar. Vacio = sin acotar (la consulta ya filtra bastante).
# Para rellenarlo: ebay.py --categorias "aparador vintage"
CATEGORIAS = []

# eBay.es se escribe en espanol; los disenadores van tal cual
BUSQUEDAS = [
    # flexos y lamparas, su lista mas grande en Wallapop
    "flexo vintage", "lampara jielde", "flexo anglepoise", "lampara industrial vintage",
    "aplique articulado vintage",
    # sillas
    "silla mid century", "silla thonet", "silla cesca", "silla teca danesa",
    # muebles de guardar (la busqueda del 2026-10-09)
    "aparador teca", "aparador vintage", "comoda vintage", "cajonera vintage",
    "credenza", "mueble bar vintage", "armario vintage", "aparador mid century",
    # escultura y bustos
    "busto bronce", "escultura brutalista", "escultura marmol vintage",
    # disenadores
    "ico parisi", "gio ponti", "joe colombo", "kazuhide takahama", "carlo hauner",
    "harvey guzzini",
    # Shaker/Judd/Barragan y lo raro
    "space age", "lampara brutalista",
    # arte venezolano ingenuo
    "pintura venezolana", "arte naif venezuela",
]


def credenciales():
    try:
        import config_local as c
    except ImportError:
        return None, "falta config_local.py"
    i = getattr(c, "EBAY_CLIENT_ID", "") or ""
    s = getattr(c, "EBAY_CLIENT_SECRET", "") or ""
    if not i or not s:
        return None, ("faltan EBAY_CLIENT_ID y EBAY_CLIENT_SECRET en config_local.py. "
                      "Son el App ID y el Cert ID del keyset de produccion "
                      "(developer.ebay.com > Application Keys)")
    return (i, s), None


def token(cred, ahora=None):
    """Token de aplicacion, reutilizado mientras le queden mas de 5 minutos."""
    ahora = ahora or time.time()
    try:
        t = json.load(open(CACHE_TOKEN, encoding="utf-8"))
        if t.get("id") == cred[0] and t["caduca"] - ahora > 300:
            return t["token"]
    except (OSError, ValueError, KeyError):
        pass
    basico = base64.b64encode(f"{cred[0]}:{cred[1]}".encode()).decode()
    r = requests.post(TOKEN_URL, timeout=30,
                      headers={"Authorization": f"Basic {basico}",
                               "Content-Type": "application/x-www-form-urlencoded"},
                      data={"grant_type": "client_credentials", "scope": ALCANCE})
    if r.status_code != 200:
        raise PermissionError(f"eBay no da token ({r.status_code}): {r.text[:200]}")
    d = r.json()
    os.makedirs(DIR_DATOS, exist_ok=True)
    with open(CACHE_TOKEN, "w", encoding="utf-8") as f:
        # solo el token y su caducidad; el secreto no sale de config_local.py
        json.dump({"id": cred[0], "token": d["access_token"],
                   "caduca": ahora + int(d.get("expires_in", 7200))}, f)
    return d["access_token"]


class Ebay:
    def __init__(self, tok):
        self.s = requests.Session()
        self.s.headers.update({"Authorization": f"Bearer {tok}",
                               "X-EBAY-C-MARKETPLACE-ID": MERCADO,
                               "Accept-Language": "es-ES", "Accept": "application/json"})
        self.n = 0
        self._ult = 0.0

    def get(self, ruta, **params):
        if self.n >= TOPE_PETICIONES:
            raise RuntimeError(f"tope de {TOPE_PETICIONES} peticiones por pasada")
        espera = PAUSA - (time.time() - self._ult)
        if espera > 0:
            time.sleep(espera)
        for intento in range(3):
            self._ult = time.time()
            self.n += 1
            r = self.s.get(API + ruta, params=params, timeout=30)
            if r.status_code == 429:
                time.sleep(10 * (intento + 1))
                continue
            if r.status_code in (401, 403):
                raise PermissionError(f"eBay {r.status_code}: {r.text[:200]}")
            if r.status_code == 404:
                return {}
            r.raise_for_status()
            return r.json()
        raise RuntimeError("eBay sigue devolviendo 429")


def filtro(tope_eur=TOPE_EUR, ue=False):
    lugar = "itemLocationRegion:EUROPEAN_UNION" if ue else "itemLocationCountry:ES"
    return f"price:[..{tope_eur}],priceCurrency:EUR,{lugar}"


def buscar(api, consulta, tope_eur=TOPE_EUR, ue=False, cuantos=100):
    params = {"q": consulta, "filter": filtro(tope_eur, ue), "limit": min(cuantos, 200)}
    if CATEGORIAS:
        params["category_ids"] = ",".join(CATEGORIAS)
    return api.get("/buy/browse/v1/item_summary/search", **params).get("itemSummaries") or []


def detalles(api, ids):
    """
    Ficha con aspectos (medidas, material, epoca).

    Primero de 20 en 20 (getItems). Pero getItems es de acceso restringido y
    una app personal recibe 403 (comprobado el 2026-10-14). Entonces se piden
    de una en una (getItem, abierto a todos) hasta agotar el tope de la pasada,
    en el orden recibido: rastrear() pone primero los anuncios sin medidas en
    el titulo, que son los que mas ganan con la ficha.
    """
    out = {}
    por_lotes = True
    for i in range(0, len(ids), 20):
        try:
            res = api.get("/buy/browse/v1/item/", item_ids=",".join(ids[i:i + 20]))
        except PermissionError:
            por_lotes = False
            break
        for it in res.get("items") or []:
            out[it["itemId"]] = it
    if por_lotes:
        return out
    for iid in ids:
        if api.n >= TOPE_PETICIONES - 2:
            break
        try:
            it = api.get("/buy/browse/v1/item/" + urllib.parse.quote(iid, safe=""))
        except (PermissionError, RuntimeError):
            break
        if it.get("itemId"):
            out[it["itemId"]] = it
    return out


# Aspectos de eBay.es que son medidas. Vienen como "120 cm", "1,2 m" o "47 in".
ASPECTO_EJE = {"anchura": "ancho", "ancho": "ancho", "longitud": "ancho", "largo": "ancho",
               "altura": "alto", "alto": "alto", "profundidad": "fondo", "fondo": "fondo",
               "width": "ancho", "height": "alto", "depth": "fondo", "length": "ancho"}
RE_VALOR = re.compile(r"(\d{1,4}(?:[.,]\d{1,2})?)\s*(cm|mm|m|in|pulgadas|\"|”)?", re.I)


def medidas_aspectos(aspectos):
    out = {}
    for a in aspectos or []:
        nombre = re.sub(r"\s*\(.*\)", "", (a.get("name") or "").lower()).strip()
        eje = ASPECTO_EJE.get(nombre)
        m = RE_VALOR.search(a.get("value") or "")
        if not eje or not m:
            continue
        v = float(m.group(1).replace(",", "."))
        u = (m.group(2) or "cm").lower()
        v *= {"mm": 0.1, "m": 100.0, "in": 2.54, "pulgadas": 2.54, '"': 2.54, "”": 2.54}.get(u, 1.0)
        if 2 < v < 400:
            out.setdefault(eje, round(v))
    return out


def foto(url, lado):
    """Las fotos de eBay se piden por tamano: .../s-l225.jpg -> s-l500, s-l1600."""
    if not url:
        return None
    return re.sub(r"/s-l\d+\.(jpg|jpeg|png|webp)", rf"/s-l{lado}.\1", url)


def normalizar(s, ficha=None, obtenido=None):
    """
    `s` es un itemSummary de la busqueda; `ficha`, la ficha completa si se pidio.
    Se queda solo con la pieza. Nada del vendedor (licencia, apartado de datos
    personales): ni nombre, ni valoraciones.
    """
    ficha = ficha or {}
    subasta = "AUCTION" in (s.get("buyingOptions") or []) and "FIXED_PRICE" not in (s.get("buyingOptions") or [])
    precio = (s.get("currentBidPrice") if subasta else None) or s.get("price") or {}
    try:
        valor = float(precio["value"])
    except (KeyError, TypeError, ValueError):
        return None
    moneda = precio.get("currency", "EUR")
    eur = round(valor * A_EUR[moneda], 2) if moneda in A_EUR else None
    if not eur or eur <= 0:
        return None

    titulo = (s.get("title") or "").strip()
    desc = re.sub(r"\s+", " ", sin_etiquetas(ficha.get("shortDescription")
                                            or s.get("shortDescription") or "")).strip()
    aspectos = ficha.get("localizedAspects") or []
    m = medidas_aspectos(aspectos)
    if len(m) >= 2:
        dims, lado = medidas_txt(m)
    else:
        dims, lado = medidas_libres(titulo + " . " + desc)
    # materiales, epoca y estilo vienen como aspectos; el resto (marca, tipo de
    # envio...) no describe la pieza
    utiles = [f"{a['name']}: {a['value']}" for a in aspectos
              if re.search(r"material|[ée]poca|estilo|a[ñn]o|d[ée]cada|color|dise[ñn]ador|fabricante",
                           a.get("name") or "", re.I)][:6]
    estado = s.get("condition") or ficha.get("condition") or ""
    texto = " . ".join(x for x in [titulo, dims, estado, " · ".join(utiles), desc[:900]] if x)

    loc = s.get("itemLocation") or ficha.get("itemLocation") or {}
    pais = (loc.get("country") or "").upper() or None
    img = (s.get("image") or {}).get("imageUrl") or (ficha.get("image") or {}).get("imageUrl")

    avisos = []
    if subasta:
        fin = (s.get("itemEndDate") or "")[:16].replace("T", " ")
        avisos.append("SUBASTA en eBay: puja actual, no precio final" + (f"; termina {fin} UTC" if fin else ""))
    if pais and pais != "ES":
        avisos.append(f"esta en {pais}: envio internacional aparte")
    if moneda != "EUR":
        avisos.append(f"precio en {moneda}; el valor en euros es aproximado")

    antes = (s.get("marketingPrice") or {}).get("originalPrice") or {}
    extra = {}
    # coste de envio, cuando eBay lo da en euros (o gratis)
    for op in s.get("shippingOptions") or ficha.get("shippingOptions") or []:
        c = op.get("shippingCost") or {}
        try:
            if c.get("currency", "EUR") == "EUR" and c.get("value") is not None:
                extra["envio"] = float(c["value"])
                break
        except (TypeError, ValueError):
            pass
    try:
        if float(antes.get("value")) > valor:
            # la rebaja la marca el propio anuncio, no un calculo nuestro
            extra["precio_anterior"] = float(antes["value"])
    except (TypeError, ValueError):
        pass

    return lote(
        "ebay", "eBay", titulo, (s.get("itemWebUrl") or "").split("?")[0], eur,
        lote=s.get("itemId"), texto=texto[:1500], imagen=foto(img, 500),
        imagen_grande=foto(img, 1600), origen="ebay-api", lado_mayor_cm=lado,
        ubicacion=loc.get("city") or pais, precio_fijo=not subasta,
        precio_original=f"{valor:.2f} {moneda}", avisos_fuente=avisos,
        obtenido=obtenido or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **extra,
    )


def rastrear(consultas=None, tope_eur=TOPE_EUR, ue=False):
    cred, error = credenciales()
    if error:
        print("EBAY:", error)
        return []
    try:
        api = Ebay(token(cred))
    except PermissionError as e:
        print("EBAY:", e)
        return []
    consultas = consultas or BUSQUEDAS
    resumenes, vistos = [], set()
    print(f"\n=== eBay.es (Browse API) · {len(consultas)} busquedas · "
          f"{'UE' if ue else 'Espana'} · hasta {tope_eur} EUR ===")
    for q in consultas:
        try:
            nuevos = [x for x in buscar(api, q, tope_eur, ue) if x.get("itemId") not in vistos]
        except PermissionError as e:
            print("  ", e)
            return []
        except requests.RequestException as e:
            # un 500 o un corte de red en UNA busqueda no aborta la pasada
            print("  ", q, e)
            continue
        vistos.update(x["itemId"] for x in nuevos)
        resumenes += nuevos
        print(f"  {len(nuevos):3d}  {q}")
    # Las medidas solo estan en la ficha. Se piden mientras quede presupuesto,
    # primero las de los anuncios que no traen medidas en el titulo.
    orden = sorted(resumenes, key=lambda x: bool(medidas_libres(x.get("title") or "")[0]))
    hueco = (TOPE_PETICIONES - api.n - 5) * 20
    fichas = detalles(api, [x["itemId"] for x in orden[:max(0, hueco)]])
    obtenido = datetime.now(timezone.utc).isoformat(timespec="seconds")
    lotes = [x for x in (normalizar(s, fichas.get(s["itemId"]), obtenido) for s in resumenes) if x]
    print(f"  TOTAL eBay: {len(lotes)} anuncios · {api.n} peticiones")
    return lotes


def categorias(texto):
    """Sugerencias de categoria de eBay.es para rellenar CATEGORIAS."""
    cred, error = credenciales()
    if error:
        print("EBAY:", error)
        return
    api = Ebay(token(cred))
    arbol = api.get("/commerce/taxonomy/v1/get_default_category_tree_id",
                    marketplace_id=MERCADO).get("categoryTreeId", ARBOL_ES)
    res = api.get(f"/commerce/taxonomy/v1/category_tree/{arbol}/get_category_suggestions", q=texto)
    for s in res.get("categorySuggestions") or []:
        c = s.get("category") or {}
        ruta = " > ".join(a.get("categoryName", "") for a in reversed(s.get("categoryTreeNodeAncestors") or []))
        print(f"  {c.get('categoryId'):>8}  {ruta} > {c.get('categoryName')}")


def guardar(lotes):
    os.makedirs(DIR_DATOS, exist_ok=True)
    datos = {"obtenido": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "lotes": lotes}
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False)
    return ARCHIVO


def cargar_si_fresco(max_horas=MAX_HORAS):
    """Los anuncios solo si tienen menos de 6 h (licencia de la API de eBay)."""
    if not os.path.exists(ARCHIVO):
        return [], "sin datos de eBay todavia"
    datos = json.load(open(ARCHIVO, encoding="utf-8"))
    t = datetime.fromisoformat(datos["obtenido"])
    horas = (datetime.now(timezone.utc) - t).total_seconds() / 3600
    if horas > max_horas:
        return [], f"datos de eBay de hace {horas:.0f} h: caducados, vuelve a pasar ebay.py"
    return datos["lotes"], f"eBay de hace {horas:.1f} h"


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--categorias":
        categorias(" ".join(args[1:]) or "aparador")
        sys.exit()
    ue = "--ue" in args
    extra = [a for a in args if not a.startswith("-")]
    lotes = rastrear(extra or None, ue=ue)
    if lotes:
        print("guardado en", guardar(lotes))
