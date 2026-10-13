# -*- coding: utf-8 -*-
"""
La tarea programada de Caxi-Vaxi: rastrea, regenera la pagina y la sube.

La lanza launchd (~/Library/LaunchAgents/com.diego.caxivaxi.plist) cuatro veces
al dia. La primera del dia hace la pasada completa; las demas solo eBay, que
caduca a las 6 h, y vuelven a subir la pagina.

    .venv/bin/python actualizar.py           decide solo (completa o solo eBay)
    .venv/bin/python actualizar.py completa  fuerza la pasada completa
    .venv/bin/python actualizar.py ebay      solo eBay y subir

Cada paso va aparte: si uno falla (una casa caida, un 403), los demas siguen.
Todo queda en datos/actualizar.log.
"""
import datetime
import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(RAIZ, ".venv", "bin", "python")
LOG = os.path.join(RAIZ, "datos", "actualizar.log")
MARCA = os.path.join(RAIZ, "datos", ".ultima_completa")

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


def toca_completa():
    hoy = datetime.date.today().isoformat()
    try:
        return open(MARCA, encoding="utf-8").read().strip() != hoy
    except OSError:
        return True


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


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else ("completa" if toca_completa() else "ebay")
    anotar(f"=== {modo} ===")
    if modo == "completa":
        correr(COMPLETA)
        with open(MARCA, "w", encoding="utf-8") as f:
            f.write(datetime.date.today().isoformat())
    else:
        correr(SOLO_EBAY)
    anotar("=== fin ===")
