# -*- coding: utf-8 -*-
"""
Prepara una busqueda para COMPARTIR: una pagina para el movil, publicable como
Artifact privado de claude.ai, donde otra persona ve las piezas y vota.

    .venv/bin/python compartir.py                 muebles de guardar
    -> datos/compartir/muebles-de-guardar/        index.html, piezas.json, m00.jpg...

Por que asi y no con la pagina de siempre:
  - La pagina publicada no puede cargar imagenes de otras webs (su CSP lo
    bloquea). Asi que se baja UNA miniatura pequena por pieza (220 x 275) y se
    juntan de cien en cien en mosaicos JPEG. La foto buena sigue en la tienda:
    cada pieza enlaza a ella. Esto es solo para esta pagina privada; el
    rastreador sigue sin guardar fotos.
  - Etsy NO entra: sus condiciones de API prohiben mostrar datos de mas de 24 h,
    y una pagina publicada se queda vieja. eBay tampoco, por lo mismo (6 h) y
    porque su licencia prohibe mezclar sus anuncios con los de otras fuentes.
  - Los votos van al almacen compartido del Artifact (capacidad db), cada
    persona en su propio documento. Si quien vota no puede escribir ahi (le
    llego un enlace publico, o no tiene cuenta), se guardan en su telefono y
    puede copiar su lista para mandarla por WhatsApp.

La seleccion es la misma que hace la pagina con el tipo "almacenaje": el
vocabulario y las exclusiones se leen de plantilla.py, no se copian.
"""
import hashlib
import io
import json
import os
import re
import sys
import time
import unicodedata
import warnings
from concurrent.futures import ThreadPoolExecutor

warnings.simplefilter("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
from PIL import Image

from config import UA
from plantilla import PLANTILLA
from puntuar import todos_los_vivos
from scraper import DIR_DATOS
import wallapop
from vista import preparar, svg

ANCHO, ALTO = 220, 275          # miniatura 4:5
COLS = FILAS = 10               # cien por mosaico
FUERA = {"etsy", "ebay"}        # fuentes que no pueden ir en una pagina publicada


def plano(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def reglas_almacenaje():
    """El vocabulario de la pagina, pasado a expresiones de Python."""
    voc = re.search(r"'almacenaje':\[(.*?)\],\s*'asiento'", PLANTILLA, re.S).group(1)
    palabras = re.findall(r"'([^']+)'", voc)
    # Python no admite un lookbehind de ancho variable: se parte en varios
    palabras = [re.sub(r"\(\?<!([^)]*)\)",
                       lambda m: "".join(f"(?<!{x})" for x in m.group(1).split("|")), p)
                for p in palabras]
    si = re.compile(r"(?:^|[^a-z0-9])(?:" + "|".join(palabras) + ")")
    no = re.compile(re.search(r"TIPOS_NO=\{almacenaje:/(.*?)/\};", PLANTILLA).group(1))
    minimo = int(re.search(r"TIPOS_MIN_CM=\{almacenaje:(\d+)\}", PLANTILLA).group(1))
    return si, no, minimo


SUBTIPOS = [
    ("comoda", r"comoda|cajoner|chests? of drawers|dresser|commode|kommode|cassett|chiffon|chifon|sinfonier|semainier|tallboy|ladekast|tansu|chest"),
    ("aparador", r"aparador|sideboard|credenza|buffet|enfilade|anrichte|dressoir|madia|lowboard|bahut|trinchero"),
    ("alto", r"highboard|cupboard|alacena|vitrin"),
    ("armario", r"armario|wardrobe|armoire|armadio|ropero|schrank"),
    ("bar", r"\bbar\b|mueble bar|mobile bar"),
    ("cabinet", r"cabinet"),
]


def subtipo(titulo):
    t = plano(titulo)
    for k, rx in SUBTIPOS:
        if re.search(rx, t):
            return k
    return "otro"


def clave(url):
    """Id corto y estable: el voto sobrevive a republicar con datos nuevos."""
    return hashlib.sha1(url.encode()).hexdigest()[:10]


def seleccion():
    lotes = json.load(open(os.path.join(DIR_DATOS, "lotes.json"), encoding="utf-8"))
    de_wallapop, _ = wallapop.cargar()
    lotes = lotes + [l for l in de_wallapop if not l.get("reservado")]
    lotes = [l for l in lotes if l.get("casa") not in FUERA]
    # solo Europa, como la pagina principal
    datos = [d for d in preparar(todos_los_vivos(lotes)) if d.get("eu") is not False]
    si, no, minimo = reglas_almacenaje()
    out = []
    for d in datos:
        t = plano(d["titulo"])
        if not si.search(t) or no.search(t):
            continue
        if d.get("d3") and max(d["d3"]) < minimo:
            continue
        if not d.get("img") or not d.get("salida"):
            continue
        out.append(d)
    out.sort(key=lambda d: (-d["g"], d["salida"]))
    return out


def miniatura(url, sesion):
    try:
        r = sesion.get(url, timeout=25)
        if r.status_code != 200:
            return None
        im = Image.open(io.BytesIO(r.content)).convert("RGB")
    except Exception:
        return None
    # recorte "cover" a 4:5, centrado
    w, h = im.size
    objetivo = ANCHO / ALTO
    if w / h > objetivo:
        nw = int(h * objetivo)
        im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w / objetivo)
        im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    return im.resize((ANCHO, ALTO), Image.LANCZOS)


def url_miniatura(d):
    u = d["img"]
    if "1stdibscdn.com" in u:
        return u.split("?")[0] + "?width=320"
    return u


def construir(nombre="muebles-de-guardar", titulo="Caxi-Vaxi de guardar"):
    piezas = seleccion()
    carpeta = os.path.join(DIR_DATOS, "compartir", nombre)
    os.makedirs(carpeta, exist_ok=True)
    print(f"{len(piezas)} piezas. Bajando miniaturas...")

    sesion = requests.Session()
    sesion.headers["User-Agent"] = UA
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=6) as ex:
        minis = list(ex.map(lambda d: miniatura(url_miniatura(d), sesion), piezas))
    fallos = sum(1 for m in minis if m is None)
    print(f"  {len(minis) - fallos} miniaturas en {time.time() - t0:.0f} s ({fallos} sin foto)")

    vacia = Image.new("RGB", (ANCHO, ALTO), (244, 244, 245))
    n_mosaicos = (len(piezas) + COLS * FILAS - 1) // (COLS * FILAS)
    for m in range(n_mosaicos):
        lienzo = Image.new("RGB", (ANCHO * COLS, ALTO * FILAS), (244, 244, 245))
        for j in range(COLS * FILAS):
            i = m * COLS * FILAS + j
            if i >= len(piezas):
                break
            lienzo.paste(minis[i] or vacia, ((j % COLS) * ANCHO, (j // COLS) * ALTO))
        lienzo.save(os.path.join(carpeta, f"m{m:02d}.jpg"), "JPEG", quality=68, optimize=True,
                    progressive=True)

    registros = []
    for i, d in enumerate(piezas):
        rebaja = next((r for r in d["porque"] if "BAJO DE PRECIO" in r), "")
        m = re.search(r"\((\d+) -> (\d+) EUR\)", rebaja)
        registros.append({
            "k": clave(d["url"]), "t": d["titulo"], "p": round(d["salida"]),
            "s": d["grupo"], "d": d.get("dims") or "", "w": d.get("lugar") or "",
            "e": d.get("ano") or "", "u": d["url"],
            "g": d["g"], "c": subtipo(d["titulo"]),
            "r": [int(m.group(1)), int(m.group(2))] if m else None,
            "f": 0 if minis[i] is None else 1,
        })
    with open(os.path.join(carpeta, "piezas.json"), "w", encoding="utf-8") as f:
        json.dump({"piezas": registros, "mosaicos": n_mosaicos, "cols": COLS, "filas": FILAS,
                   "fecha": time.strftime("%d/%m/%Y")}, f, ensure_ascii=False, separators=(",", ":"))

    html = (PAGINA.replace("__TITULO__", titulo)
            .replace("__BALLENA__", svg("cachalote.svg")))
    with open(os.path.join(carpeta, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  listo: {carpeta}  ({n_mosaicos} mosaicos)")
    return carpeta, n_mosaicos


PAGINA = r"""<title>__TITULO__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600&display=swap">
<style>
/* Una rejilla de fichas para el pulgar: foto, precio y un corazon. El detalle
   sube desde abajo. Misma paleta que Caxi-Vaxi (Azul Klein). */
:root{
  --yeso:#F4F4F5; --caja:#FFFFFF; --tinta:#0A0A0B; --gris:#52525B; --borde:#E4E4E7;
  --muro:#FFFFFF; --muro-tinta:#0A0A0B; --rosa:#1E3BFF; --verde:#1E3BFF; --hueco:#FFFFFF;
  --ui:'Instrument Sans',system-ui,-apple-system,sans-serif;
  --etq:'Instrument Sans',system-ui,-apple-system,sans-serif;
}
@media (prefers-color-scheme:dark){ :root:not([data-theme="light"]){
  --yeso:#0B0B0D; --caja:#161618; --tinta:#F4F4F5; --gris:#A1A1AA; --borde:#26262B;
  --muro:#0B0B0D; --muro-tinta:#F4F4F5; --rosa:#7286FF; --verde:#7286FF; --hueco:#0B0B0D;
  color-scheme:dark; }}
:root[data-theme="dark"]{
  --yeso:#0B0B0D; --caja:#161618; --tinta:#F4F4F5; --gris:#A1A1AA; --borde:#26262B;
  --muro:#0B0B0D; --muro-tinta:#F4F4F5; --rosa:#7286FF; --verde:#7286FF; --hueco:#0B0B0D;
  color-scheme:dark; }
*{box-sizing:border-box}
body{background:var(--yeso);color:var(--tinta);font-family:var(--ui);font-size:14px;margin:0}
button{font:inherit;color:inherit}
a{color:inherit}
:focus-visible{outline:2px solid var(--rosa);outline-offset:2px}

.muro{position:sticky;top:env(safe-area-inset-top,0px);z-index:20;background:var(--muro);
  color:var(--muro-tinta);padding:10px 16px 0}
.fila1{display:flex;align-items:center;gap:10px}
.ballena{width:40px;display:inline-flex;flex:none}
.ballena svg{width:100%;height:auto;display:block}
h1{margin:0;font-size:17px;font-weight:600;letter-spacing:-.01em;line-height:1}
h1 em{font-style:normal;opacity:.55}
.cuenta{margin-left:auto;font-family:var(--etq);font-size:12px;letter-spacing:.04em;
  font-variant-numeric:tabular-nums;text-align:right;opacity:.85}
.quienes{display:flex;gap:6px;align-items:center;font-family:var(--etq);font-size:12px;
  padding-top:6px;min-height:26px;opacity:.9}
.quienes img{width:20px;height:20px;border-radius:50%;display:block}
.filtros{display:flex;gap:6px;overflow-x:auto;padding:8px 0 10px;scrollbar-width:none}
.filtros::-webkit-scrollbar{display:none}
.chip{flex:none;font-family:var(--etq);font-size:12.5px;letter-spacing:.03em;padding:7px 11px;
  border:1px solid var(--borde);background:transparent;color:var(--muro-tinta);
  border-radius:999px;cursor:pointer;white-space:nowrap}
.chip.on{background:var(--muro-tinta);color:var(--muro);border-color:var(--muro-tinta)}
.sep{flex:none;width:1px;background:var(--borde);margin:4px 2px}
.muro{border-bottom:1px solid var(--borde)}
.co{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;vertical-align:-4px}
.v.si.on .co{fill:currentColor}
.cargando{text-align:center;color:var(--gris);padding:48px 16px}

.barra{display:flex;gap:8px;padding:12px 16px 4px;align-items:center;flex-wrap:wrap}
.barra input{flex:1;min-width:0;font:inherit;font-size:15px;padding:9px 11px;border:1px solid var(--borde);
  background:var(--caja);color:var(--tinta);border-radius:8px}
.barra select{font:inherit;font-size:13px;padding:9px 8px;border:1px solid var(--borde);
  background:var(--caja);color:var(--tinta);border-radius:8px}
.aviso{margin:8px 16px 0;padding:10px 12px;border-radius:8px;background:var(--caja);
  border:1px solid var(--borde);font-size:13px;line-height:1.45;color:var(--gris)}
.aviso b{color:var(--tinta)}
.aviso button{margin-top:8px;font-family:var(--etq);font-size:12.5px;padding:7px 12px;border-radius:999px;
  border:1px solid var(--rosa);background:var(--rosa);color:#fff;cursor:pointer}

.rejilla{display:grid;grid-template-columns:repeat(auto-fill,minmax(158px,1fr));gap:12px;
  padding:12px 16px 24px}
.ficha{background:var(--caja);border:1px solid var(--borde);border-radius:10px;overflow:hidden;
  display:flex;flex-direction:column;min-width:0}
.ficha.no{opacity:.45}
.foto{display:block;width:100%;aspect-ratio:4/5;background-color:var(--borde);
  background-repeat:no-repeat;border:0;padding:0;cursor:pointer;position:relative}
.sello{position:absolute;left:8px;top:8px;font-family:var(--etq);font-size:10.5px;letter-spacing:.06em;
  text-transform:uppercase;background:var(--rosa);color:#fff;padding:3px 7px;border-radius:4px}
.cartela{padding:8px 10px 10px;display:flex;flex-direction:column;gap:4px;min-width:0;flex:1}
.precio{font-weight:800;font-size:16px;font-variant-numeric:tabular-nums;display:flex;
  align-items:baseline;gap:6px}
.precio s{font-weight:400;font-size:12px;color:var(--gris)}
.nombre{font-size:13px;line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;
  -webkit-box-orient:vertical;overflow:hidden}
.meta{font-family:var(--etq);font-size:11.5px;color:var(--gris);line-height:1.35}
.votos{display:flex;gap:6px;margin-top:auto;padding-top:6px;align-items:center}
.v{flex:1;border:1px solid var(--borde);background:transparent;border-radius:999px;padding:7px 0;
  font-size:13px;cursor:pointer;font-family:var(--etq);letter-spacing:.02em}
.v.si.on{background:var(--rosa);border-color:var(--rosa);color:#fff}
.v.no.on{background:var(--tinta);border-color:var(--tinta);color:var(--yeso)}
.otros{display:flex;gap:3px;min-height:18px;align-items:center;font-family:var(--etq);
  font-size:11px;color:var(--gris)}
.otros img{width:16px;height:16px;border-radius:50%}
.mas{display:block;margin:0 auto 32px;font-family:var(--etq);font-size:13px;padding:10px 18px;
  border:1px solid var(--borde);background:var(--caja);border-radius:999px;cursor:pointer}
.nada{text-align:center;color:var(--gris);padding:40px 16px;font-family:var(--etq);line-height:1.5}

.velo{position:fixed;inset:0;z-index:40;background:rgba(10,10,8,.55);display:flex;align-items:flex-end;
  justify-content:center}
.hoja{background:var(--caja);color:var(--tinta);width:100%;max-width:560px;max-height:92%;overflow-y:auto;
  border-radius:16px 16px 0 0;padding:14px 16px calc(18px + env(safe-area-inset-bottom,0px))}
.hoja .foto{max-width:300px;margin:0 auto;border-radius:8px;cursor:default}
.hoja h2{font-size:17px;line-height:1.3;margin:12px 0 4px;text-wrap:balance}
.hoja dl{display:grid;grid-template-columns:auto 1fr;gap:4px 12px;margin:10px 0;font-size:13px}
.hoja dt{font-family:var(--etq);color:var(--gris);text-transform:uppercase;font-size:11px;
  letter-spacing:.06em;padding-top:2px}
.hoja dd{margin:0;min-width:0;overflow-wrap:anywhere}
.ir{display:block;text-align:center;margin-top:10px;padding:11px;border-radius:999px;
  background:var(--muro);color:var(--muro-tinta);text-decoration:none;font-family:var(--etq);font-size:13.5px}
.cerrar{float:right;border:0;background:transparent;font-size:22px;line-height:1;cursor:pointer;
  padding:2px 6px;color:var(--gris)}
.copia{width:100%;min-height:140px;font:inherit;font-size:12px;margin-top:8px;padding:8px;
  border:1px solid var(--borde);border-radius:8px;background:var(--yeso);color:var(--tinta)}
@media (prefers-reduced-motion:no-preference){ .hoja{animation:sube .18s ease-out} }
@keyframes sube{from{transform:translateY(24px);opacity:.6}to{transform:none;opacity:1}}
</style>

<header class="muro">
  <div class="fila1">
    <span class="ballena" aria-hidden="true">__BALLENA__</span>
    <h1>Caxi-Vaxi</h1>
    <div class="cuenta" id="cuenta">cargando…</div>
  </div>
  <div class="quienes" id="quienes"></div>
  <div class="filtros" id="filtros" role="toolbar" aria-label="Filtros"></div>
</header>

<div class="barra">
  <input id="q" type="search" placeholder="buscar: teca, roble, años 60…" aria-label="Buscar por palabra">
  <select id="orden" aria-label="Orden">
    <option value="g">sugeridos</option>
    <option value="p">más baratos</option>
    <option value="pd">más caros</option>
  </select>
</div>
<div id="aviso"></div>
<div class="cargando" id="cargando">Cargando las piezas, tarda unos segundos…</div>
<main class="rejilla" id="rejilla" aria-live="polite"></main>
<div class="nada" id="nada" hidden>Nada con estos filtros. Quita alguno.</div>
<button class="mas" id="mas" hidden>ver más</button>
<div class="velo" id="velo" hidden></div>

<script>
const $=s=>document.querySelector(s);
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const plano=s=>String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');
const TIPOS=[['','todo'],['comoda','cómodas'],['aparador','aparadores'],['armario','armarios'],
  ['alto','altos y vitrinas'],['bar','mueble bar'],['cabinet','cabinets']];
const PRECIOS=[[0,'cualquier precio'],[200,'hasta 200 €'],[400,'hasta 400 €'],[600,'hasta 600 €']];
const E={tipo:'',tope:0,q:'',orden:'g',gustan:false,ocultarNo:false};
let P=[], META={}, vistos=[], pintadas=0;
const POR_TANDA=60;

/* ---------- votos: almacen compartido si se puede, telefono si no ---------- */
const LS='cacharrotes.compartir.votos';
let mios={}; try{ mios=JSON.parse(localStorage.getItem(LS)||'{}')||{}; }catch(e){}
let otros={};          /* id de persona -> {clave: 'si'|'no'} */
let yo=null, db=null, user=null, modo='local', perfiles={}, primera=true;
function guardarLocal(){ try{ localStorage.setItem(LS,JSON.stringify(mios)); }catch(e){} }

let escribiendo=false, pendiente=false, temporizador=null;
function programarEscritura(){
  if(modo!=='compartido')return;
  clearTimeout(temporizador); temporizador=setTimeout(escribir,700);
}
async function escribir(){
  if(escribiendo){ pendiente=true; return; }
  escribiendo=true;
  try{ await db.doc('votos/'+yo).set({v:{...mios},t:Date.now()}); }
  catch(e){
    if(e&&(e.code==='invalid_argument'||e.code==='not_granted'||e.code==='revoked')){
      modo='local'; pintarAviso(); }
  }
  escribiendo=false;
  if(pendiente){ pendiente=false; escribir(); }
}
function votar(k,valor){
  if(mios[k]===valor)delete mios[k]; else mios[k]=valor;
  guardarLocal(); programarEscritura();
  document.querySelectorAll('[data-k="'+k+'"]').forEach(pintarVotos);
  if(E.gustan||E.ocultarNo)contar();
}
function votosDe(k){
  const r=[]; for(const id in otros){ if(id!==yo&&otros[id][k])r.push([id,otros[id][k]]); } return r;
}

async function conectar(){
  if(!window.claude||!claude.use)return;
  [db,user]=await Promise.all([claude.use('db'),claude.use('user')]);
  if(!db||!user){ pintarAviso(); return; }
  yo=await user.id();
  if(!yo){ pintarAviso(); return; }
  modo='compartido';
  db.collection('votos').onSnapshot(async snap=>{
    const nuevo={};
    snap.docs.forEach(d=>{ const b=d.data(); if(b&&b.v)nuevo[d.id]=b.v; });
    /* solo la primera vez: se juntan los votos del almacen con los de este
       telefono. Despues manda este telefono, que es el que escribe lo suyo. */
    if(primera){ primera=false; mios={...(nuevo[yo]||{}),...mios}; guardarLocal(); }
    otros=nuevo;
    const ids=Object.keys(otros); if(yo&&!ids.includes(yo))ids.push(yo);
    perfiles=ids.length?await user.profiles(ids):{};
    pintarQuienes(); document.querySelectorAll('.ficha').forEach(pintarVotos); contar();
  },()=>{ modo='local'; pintarAviso(); });
  if(Object.keys(mios).length)programarEscritura();
  pintarAviso();
  if(await user.isOwner())pintarAviso(true);
}
function pintarQuienes(){
  const ids=Object.keys(otros).filter(id=>Object.values(otros[id]).some(v=>v==='si'));
  const q=$('#quienes'); q.textContent='';
  if(!ids.length){ q.textContent=modo==='compartido'?'Toca el corazón en lo que te guste. Lo vemos los dos.':''; return; }
  q.append('Han elegido: ');
  ids.forEach(id=>{ const p=perfiles[id]||{}; const i=document.createElement('img');
    i.src=p.avatarUrl||''; i.alt=''; i.title=p.name||'alguien'; q.append(i);
    const n=document.createElement('span'); n.textContent=(p.isMe?'tú':(p.name||'alguien').split(' ')[0])
      +' ('+Object.values(otros[id]).filter(v=>v==='si').length+')'; q.append(n); });
}
function pintarAviso(soyDueno){
  const a=$('#aviso');
  if(soyDueno){
    a.innerHTML='<div class="aviso"><b>Para que ella vote desde su móvil</b>, compártela invitándola por correo como Editora. '
      +'Con un enlace público solo podría mirar.</div>'; return; }
  if(modo==='compartido'){ a.innerHTML=''; return; }
  a.innerHTML='<div class="aviso"><b>No hace falta cuenta ni iniciar sesión.</b> Si claude.ai te pide '
    +'«Sign in», ignóralo: la página funciona igual. Toca el corazón en lo que te guste y, al terminar, '
    +'envíale tu lista a Diego.<br><button id="copiar">Enviar mi lista</button></div>';
  $('#copiar').onclick=copiar;
}
function copiar(){
  const fav=P.filter(x=>mios[x.k]==='si');
  const txt=fav.length?('Mis favoritos de Caxi-Vaxi ('+fav.length+'):\n\n'
    +fav.map(x=>'- '+x.t+' · '+x.p+' €\n  '+x.u).join('\n')):'Aún no has marcado ninguno con el corazón.';
  const fin=()=>abrirHoja('<button class="cerrar" id="x" aria-label="Cerrar"><svg class="co" viewBox="0 0 24 24" aria-hidden="true"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg></button>'
    +'<h2>Tu lista</h2><p class="meta">Si no se copió sola, mantén pulsado el texto y cópialo.</p>'
    +'<textarea class="copia" id="txt" readonly>'+esc(txt)+'</textarea>');
  if(fav.length&&navigator.share){ navigator.share({title:'Mis favoritos de Caxi-Vaxi',text:txt}).catch(()=>{}); return; }
  try{ navigator.clipboard.writeText(txt).then(()=>{ fin(); $('#txt').insertAdjacentHTML('beforebegin','<p class="meta">Copiada. Pégala en WhatsApp.</p>'); },fin); }
  catch(e){ fin(); }
}

/* ---------- filtros y rejilla ---------- */
function chips(){
  const f=$('#filtros');
  f.innerHTML=TIPOS.map(([k,n])=>'<button class="chip'+(E.tipo===k?' on':'')+'" data-tipo="'+k+'">'+n+'</button>').join('')
    +'<span class="sep"></span>'
    +PRECIOS.map(([v,n])=>'<button class="chip'+(E.tope===v?' on':'')+'" data-tope="'+v+'">'+n+'</button>').join('')
    +'<span class="sep"></span>'
    +'<button class="chip'+(E.gustan?' on':'')+'" data-gustan="1">Favoritos</button>';
}
$('#filtros').addEventListener('click',e=>{
  const b=e.target.closest('.chip'); if(!b)return;
  if('tipo' in b.dataset)E.tipo=b.dataset.tipo;
  if('tope' in b.dataset)E.tope=+b.dataset.tope;
  if(b.dataset.gustan)E.gustan=!E.gustan;
  if(b.dataset.ocultar)E.ocultarNo=!E.ocultarNo;
  chips(); filtrar();
});
let tq=null; $('#q').addEventListener('input',e=>{ clearTimeout(tq); tq=setTimeout(()=>{ E.q=plano(e.target.value).trim(); filtrar(); },200); });
$('#orden').addEventListener('change',e=>{ E.orden=e.target.value; filtrar(); });

function pasa(x){
  if(E.tipo&&x.c!==E.tipo)return false;
  if(E.tope&&x.p>E.tope)return false;
  if(E.q&&!E.q.split(/\s+/).every(w=>x._t.includes(w)))return false;
  if(E.ocultarNo&&mios[x.k]==='no')return false;
  if(E.gustan&&!(mios[x.k]==='si'||votosDe(x.k).some(v=>v[1]==='si')))return false;
  return true;
}
function contar(){ $('#cuenta').innerHTML=vistos.filter(pasa).length+' de '+P.length+'<br>'+esc(META.fecha||''); }
function filtrar(){
  vistos=P.filter(pasa);
  if(E.orden==='p')vistos.sort((a,b)=>a.p-b.p); else if(E.orden==='pd')vistos.sort((a,b)=>b.p-a.p);
  else vistos.sort((a,b)=>a.i-b.i);
  $('#rejilla').innerHTML=''; pintadas=0; mas(); contar();
  $('#nada').hidden=vistos.length>0;
}
function fondo(x){
  const n=META.cols*META.filas, m=Math.floor(x.i/n), j=x.i%n;
  const c=j%META.cols, f=Math.floor(j/META.cols);
  return 'background-image:url(m'+String(m).padStart(2,'0')+'.jpg);background-size:'+(META.cols*100)+'% '+(META.filas*100)+'%;'
    +'background-position:'+(c/(META.cols-1)*100)+'% '+(f/(META.filas-1)*100)+'%';
}
const PAIS={'Reino Unido':'UK','Estados Unidos':'EE. UU.','República Checa':'Chequia','Países Bajos':'P. Bajos'};
function ficha(x){
  const meta=[x.d,x.e,PAIS[x.w]||x.w,x.s].filter(Boolean).map(esc).join(' · ');
  return '<article class="ficha" data-k="'+x.k+'">'
    +'<button class="foto" style="'+fondo(x)+'" data-i="'+x.i+'" aria-label="Ver '+esc(x.t)+'">'
    +(x.r?'<span class="sello">rebajado</span>':'')+'</button>'
    +'<div class="cartela"><div class="precio">'+x.p+' €'+(x.r?' <s>'+x.r[0]+' €</s>':'')+'</div>'
    +'<div class="nombre">'+esc(x.t)+'</div><div class="meta">'+meta+'</div>'
    +'<div class="otros"></div>'
    +'<div class="votos"><button class="v si" data-v="si" aria-label="Me gusta"><svg class="co" viewBox="0 0 24 24" aria-hidden="true"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg> Me gusta</button></div></div></article>';
}
function pintarVotos(el){
  const k=el.dataset.k, mio=mios[k];
  el.querySelectorAll('.v').forEach(b=>b.classList.toggle('on',b.dataset.v===mio));
  if(el.classList.contains('ficha'))el.classList.toggle('no',mio==='no');
  const o=el.querySelector('.otros'); if(!o)return;
  o.textContent='';
  votosDe(k).filter(v=>v[1]==='si').forEach(([id])=>{ const p=perfiles[id]||{};
    const i=document.createElement('img'); i.src=p.avatarUrl||''; i.alt=''; o.append(i);
    const s=document.createElement('span'); s.textContent='le gusta a '+((p.name||'alguien').split(' ')[0]); o.append(s); });
}
function mas(){
  const r=$('#rejilla'), hasta=Math.min(vistos.length,pintadas+POR_TANDA);
  r.insertAdjacentHTML('beforeend',vistos.slice(pintadas,hasta).map(ficha).join(''));
  [...r.children].slice(pintadas).forEach(pintarVotos);
  pintadas=hasta; $('#mas').hidden=pintadas>=vistos.length;
}
$('#mas').onclick=mas;
if('IntersectionObserver' in window)new IntersectionObserver(es=>{ if(es[0].isIntersecting&&!$('#mas').hidden)mas(); },{rootMargin:'800px'}).observe($('#mas'));

$('#rejilla').addEventListener('click',e=>{
  const v=e.target.closest('.v'); if(v){ votar(v.closest('[data-k]').dataset.k,v.dataset.v); return; }
  const f=e.target.closest('.foto'); if(f)detalle(P[+f.dataset.i]);
});

/* ---------- detalle ---------- */
function abrirHoja(html){
  const velo=$('#velo'); velo.innerHTML='<div class="hoja" role="dialog" aria-modal="true">'+html+'</div>';
  velo.hidden=false; document.body.style.overflow='hidden';
  const x=$('#x'); if(x){ x.onclick=cerrar; x.focus(); }
}
function cerrar(){ $('#velo').hidden=true; $('#velo').innerHTML=''; document.body.style.overflow=''; }
$('#velo').addEventListener('click',e=>{
  if(e.target.id==='velo')cerrar();
  const v=e.target.closest('.v'); if(v)votar(v.closest('[data-k]').dataset.k,v.dataset.v);
});
document.addEventListener('keydown',e=>{ if(e.key==='Escape'&&!$('#velo').hidden)cerrar(); });
const TIENDA=u=>u.includes('pamono')?'Pamono':u.includes('1stdibs')?'1stDibs':u.includes('oblist')?'The Oblist':'la web';
function detalle(x){
  const filas=[['precio',x.p+' €'+(x.r?' (antes '+x.r[0]+' €)':'')],['medidas',x.d||'no las da'],
    ['época',x.e],['envía desde',x.w],['tienda',x.s]].filter(f=>f[1]);
  abrirHoja('<button class="cerrar" id="x" aria-label="Cerrar"><svg class="co" viewBox="0 0 24 24" aria-hidden="true"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg></button>'
    +'<div class="foto" style="'+fondo(x)+'" role="img" aria-label="'+esc(x.t)+'"></div>'
    +'<h2>'+esc(x.t)+'</h2>'
    +'<dl>'+filas.map(f=>'<dt>'+f[0]+'</dt><dd>'+esc(f[1])+'</dd>').join('')+'</dl>'
    +'<div data-k="'+x.k+'"><div class="otros"></div><div class="votos"><button class="v si" data-v="si"><svg class="co" viewBox="0 0 24 24" aria-hidden="true"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg> Me gusta</button></div></div>'
    +'<a class="ir" href="'+esc(x.u)+'" target="_blank" rel="noopener">Ver fotos en '+esc(x.s||TIENDA(x.u))+'</a>'
    +'<p class="meta" style="margin-top:10px">El precio es sin envío. En subastas se suma la comisión de la casa.</p>');
  pintarVotos($('#velo [data-k]'));
}

/* ---------- arranque ---------- */
fetch('piezas.json').then(r=>r.json()).then(j=>{
  META=j; P=j.piezas.map((x,i)=>({...x,i,_t:plano(x.t+' '+x.d+' '+x.e+' '+x.w+' '+x.s)}));
  $('#cargando').hidden=true; chips(); filtrar();
}).catch(()=>{ $('#cargando').textContent='No se pudieron cargar las piezas. Recarga la página.'; });
pintarAviso(); conectar();
</script>
"""

if __name__ == "__main__":
    construir()
