# -*- coding: utf-8 -*-
"""
Actualiza Caxi-Vaxi: rastrea, regenera la pagina y la sube a la web.

NO hay tarea programada (Diego, 2026-10-14: muchas veces no la va a usar). La
lanza la app Caxi-Vaxi al abrirse, en segundo plano, y solo hace lo que haga
falta:
  - pasada completa si la ultima tiene mas de 24 h (unos 40 min);
  - si no, solo eBay si sus datos tienen mas de 6 h (su licencia no deja
    mostrar nada mas viejo; tarda un minuto);
  - si todo esta fresco, nada.
Ningun paso gasta tokens de Claude: son peticiones a las webs y a las APIs.

    .venv/bin/python actualizar.py           si-toca: decide solo
    .venv/bin/python actualizar.py completa  fuerza la pasada completa
    .venv/bin/python actualizar.py ebay      solo eBay y subir
    ... --avisar                             notificacion de macOS al empezar y al acabar

Cada paso va aparte: si uno falla (una casa caida, un 403), los demas siguen.
Todo queda en datos/actualizar.log.
"""
import datetime
import json
import os
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(RAIZ, ".venv", "bin", "python")
LOG = os.path.join(RAIZ, "datos", "actualizar.log")
MARCA = os.path.join(RAIZ, "datos", ".ultima_completa")
CERROJO = os.path.join(RAIZ, "datos", ".actualizando")
HORAS_COMPLETA = 24
HORAS_EBAY = 6

COMPLETA = [
    ("subastas", ["run.py"], 3600),
    ("shopify", ["shopify.py"], 1800),
    ("pamono y 1stdibs", ["tiendas.py"], 3600),
    ("etsy", ["etsy.py"], 900),
    ("wallapop", ["wallapop.py"], 900),
    ("ebay", ["ebay.py"], 900),
    ("subir", ["publicar.py"], 900),
]
SOLO_EBAY = [
    ("ebay", ["ebay.py"], 900),
    ("subir", ["publicar.py"], 900),
]


def anotar(texto):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M}  {texto}\n")


def horas_desde(iso):
    """Horas desde una fecha ISO. Acepta tambien 'AAAA-MM-DD' (marcas viejas)."""
    t = datetime.datetime.fromisoformat(iso)
    if t.tzinfo is None:
        t = t.astimezone()
    return (datetime.datetime.now(datetime.timezone.utc) - t).total_seconds() / 3600


def toca_completa():
    try:
        return horas_desde(open(MARCA, encoding="utf-8").read().strip()) > HORAS_COMPLETA
    except (OSError, ValueError):
        return True


def toca_ebay():
    """Solo si hay claves y los datos de eBay pasan de 6 h (o no hay)."""
    sys.path.insert(0, RAIZ)
    try:
        import ebay
        if ebay.credenciales()[0] is None:
            return False
        datos = json.load(open(ebay.ARCHIVO, encoding="utf-8"))
        return horas_desde(datos["obtenido"]) > HORAS_EBAY
    except Exception:   # noqa: BLE001 - sin archivo o ilegible: se intenta
        return True


def avisar(texto):
    """Notificacion de macOS. Si falla, no pasa nada."""
    try:
        subprocess.run(["osascript", "-e",
                        f'display notification "{texto}" with title "Caxi-Vaxi"'],
                       timeout=10, capture_output=True)
    except Exception:   # noqa: BLE001
        pass


def tomar_cerrojo():
    """Una actualizacion a la vez: abrir la app dos veces no lanza dos pasadas."""
    try:
        if time.time() - os.path.getmtime(CERROJO) < 2 * 3600:
            return False
    except OSError:
        pass
    with open(CERROJO, "w") as f:
        f.write(str(os.getpid()))
    return True


def soltar_cerrojo():
    try:
        os.unlink(CERROJO)
    except OSError:
        pass


def correr(pasos):
    for nombre, args, limite in pasos:
        anotar(f"empieza {nombre}")
        try:
            r = subprocess.run([PY, "-W", "ignore"] + args, cwd=RAIZ, timeout=limite,
                               capture_output=True, text=True)
            cola = (r.stdout or "").strip().splitlines()[-3:]
            anotar(f"  {nombre}: salida {r.returncode} | " + " / ".join(cola)[:300])
        except subprocess.TimeoutExpired:
            anotar(f"  {nombre}: se paso de {limite} s, se corta")
        except Exception as e:   # noqa: BLE001 - un paso roto no para los demas
            anotar(f"  {nombre}: fallo {type(e).__name__}: {e}")


def decidir(modo):
    if modo != "si-toca":
        return modo
    if toca_completa():
        return "completa"
    return "ebay" if toca_ebay() else None


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    con_aviso = "--avisar" in sys.argv
    modo = decidir(args[0] if args else "si-toca")
    if modo is None:
        anotar("=== al dia: nada que hacer ===")
        sys.exit(0)
    if not tomar_cerrojo():
        anotar(f"=== {modo}: ya hay una actualizacion en marcha ===")
        sys.exit(0)
    try:
        anotar(f"=== {modo} ===")
        if con_aviso:
            avisar("Actualizando todo (unos 40 min). Te aviso al acabar." if modo == "completa"
                   else "Actualizando eBay (un minuto).")
        if modo == "completa":
            correr(COMPLETA)
            with open(MARCA, "w", encoding="utf-8") as f:
                f.write(datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"))
        else:
            correr(SOLO_EBAY[:1])
            # si eBay no trajo nada nuevo (claves sin activar, caida), la web
            # ya esta como estaria: no se sube para nada
            if toca_ebay():
                anotar("  eBay no trajo datos nuevos: no se sube nada")
                con_aviso = False
            else:
                correr(SOLO_EBAY[1:])
        anotar("=== fin ===")
        if con_aviso:
            avisar("Ya esta al dia, en el Mac y en la web. Recarga la pagina.")
    finally:
        soltar_cerrojo()
