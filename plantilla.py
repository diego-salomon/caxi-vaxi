# -*- coding: utf-8 -*-
"""
Plantilla HTML de la vista: el buscador de Caxi-Vaxi.

QUE ES
------
Un solo buscador para todos los portales donde Diego busca muebles y arte:
subastas de Madrid, tiendas, Pamono, 1stDibs, Etsy, eBay y Wallapop. Escribe
"silla", pone sus limites y ve las sillas de todos a la vez, sin ir pagina por
pagina. Por defecto, solo Europa.

SISTEMA DE DISENO
-----------------
Estructura de Juddaun (Judd + Braun: objetos repetidos en un campo, regla de
1 px, un solo acento, esquinas rectas, sin emoji) con la paleta que eligio
Diego el 2026-10-13: "Azul Klein". Blanco puro, grises frios, tinta casi
negra y un azul Klein electrico para lo que se toca y lo que le gusta. Nada
de crema ni naranja.

  - Una sola familia, Instrument Sans, con cifras tabulares para precios.
  - La ficha solo lleva hechos de la pieza: portal, ubicacion, titulo, ano,
    medidas, materiales, precio y envio. Lo que no se sabe no se menciona.
  - Un solo voto: me gusta.
  - Filtros como Pamono y 1stDibs: que busco, precio minimo y maximo,
    medidas, material, epoca, color, pais y rebajas.
"""

PLANTILLA = r"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Caxi-Vaxi</title>
<meta name="description" content="Buscador personal de muebles y arte vintage en subastas, tiendas y portales de Europa.">
<meta name="robots" content="noindex,nofollow">
<meta name="theme-color" content="#FFFFFF" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0B0B0D" media="(prefers-color-scheme: dark)">
<link rel="icon" href="__FAVICON__">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600&display=swap">
<style>
/* === TOKENS: Azul Klein === */
:root{
  --bg:#FFFFFF; --surface:#F4F4F5; --line:#E4E4E7; --line-strong:#D4D4D8;
  --ink:#0A0A0B; --ink-2:#52525B; --ink-3:#71717A;
  --accent:#1E3BFF; --accent-hover:#1430E6; --accent-soft:#EEF1FF; --on-accent:#FFFFFF;
  --wash:rgba(10,10,11,.05); --scrim:rgba(10,10,11,.44);
  --lifted:0 1px 0 var(--line); --floating:0 16px 40px rgba(10,10,11,.16);
  --f:'Instrument Sans',ui-sans-serif,sans-serif;
  --t1:120ms; --t2:180ms; --t3:260ms; --ease:cubic-bezier(.2,0,0,1);
  --ancho:280px;
  color-scheme:light;
}
@media (prefers-color-scheme:dark){ :root:not([data-theme="light"]){
  --bg:#0B0B0D; --surface:#161618; --line:#26262B; --line-strong:#34343B;
  --ink:#F4F4F5; --ink-2:#A1A1AA; --ink-3:#8B8B94;
  --accent:#7286FF; --accent-hover:#8A9BFF; --accent-soft:#1A1F3D; --on-accent:#0B0B0D;
  --wash:rgba(244,244,245,.06); --scrim:rgba(0,0,0,.6); --floating:0 16px 40px rgba(0,0,0,.5);
  color-scheme:dark;
}}
:root[data-theme="dark"]{
  --bg:#0B0B0D; --surface:#161618; --line:#26262B; --line-strong:#34343B;
  --ink:#F4F4F5; --ink-2:#A1A1AA; --ink-3:#8B8B94;
  --accent:#7286FF; --accent-hover:#8A9BFF; --accent-soft:#1A1F3D; --on-accent:#0B0B0D;
  --wash:rgba(244,244,245,.06); --scrim:rgba(0,0,0,.6); --floating:0 16px 40px rgba(0,0,0,.5);
  color-scheme:dark;
}

/* === BASE === */
*{box-sizing:border-box}
/* IMPRESCINDIBLE. Sin esto, cualquier regla con display anula el atributo
   hidden y el velo del detalle queda siempre encima. */
[hidden]{display:none!important}
html{scrollbar-color:var(--line-strong) transparent}
body{margin:0;background:var(--bg);color:var(--ink);font:400 15px/1.5 var(--f);
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;font-variant-numeric:tabular-nums}
::selection{background:var(--accent);color:var(--on-accent)}
button,input,select{font:inherit;color:inherit}
input{caret-color:var(--accent)}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.ico{width:20px;height:20px;flex:none;fill:none;stroke:currentColor;stroke-width:1.75;
  stroke-linecap:round;stroke-linejoin:round;display:block}
.envoltura{max-width:1600px;margin:0 auto;padding:0 32px}
.etq{font-size:12px;font-weight:500;letter-spacing:.04em;text-transform:uppercase;color:var(--ink-3)}

/* === BARRA: marca, buscador y tres acciones; pegada arriba === */
.barra{position:sticky;top:0;z-index:30;background:var(--bg);box-shadow:var(--lifted)}
.fila1{display:flex;align-items:center;gap:16px;height:72px}
.marca{display:flex;align-items:center;gap:10px;margin:0;font-size:18px;font-weight:600;letter-spacing:-.01em;
  white-space:nowrap;color:var(--ink);text-decoration:none}
.marca .ballena{display:block;width:44px;color:var(--ink);--hueco:var(--bg)}
.marca svg,.ballena-grande svg{width:100%;height:auto;display:block}
.buscador{position:relative;flex:1;max-width:640px;margin:0 auto}
.buscador .ico{position:absolute;left:14px;top:12px;color:var(--ink-3);pointer-events:none}
.buscador input{width:100%;height:44px;padding:0 16px 0 44px;border-radius:999px;border:1px solid var(--line);
  background:var(--surface);font-size:15px;transition:border-color var(--t1) var(--ease),background var(--t1) var(--ease)}
.buscador input:hover{border-color:var(--line-strong)}
.buscador input:focus{background:var(--bg);border-color:var(--accent);outline:none}
.buscador input::placeholder{color:var(--ink-3)}
.acciones-barra{display:flex;gap:4px}
.boton{display:inline-flex;align-items:center;justify-content:center;gap:8px;height:40px;padding:0 14px;
  border-radius:999px;border:1px solid transparent;background:transparent;color:var(--ink);
  font-size:14px;font-weight:500;cursor:pointer;white-space:nowrap;text-decoration:none;
  transition:background var(--t1) var(--ease),color var(--t1) var(--ease),border-color var(--t1) var(--ease)}
.boton:hover{background:var(--wash)}
.boton.on{background:var(--ink);color:var(--bg)}
.boton.primario{background:var(--accent);color:var(--on-accent)}
.boton.primario:hover{background:var(--accent-hover)}
.boton.borde{border-color:var(--line-strong)}
.boton .n{min-width:18px;height:18px;padding:0 5px;border-radius:9px;background:var(--accent);color:var(--on-accent);
  font-size:11px;line-height:18px;text-align:center}
.boton.on .n{background:var(--on-accent);color:var(--accent)}

.acciones-barra{align-items:center}
.acciones-barra .total{margin:0 8px 0 12px}
.grupo.ancho{grid-column:1/-1}
select{height:36px;border-radius:999px;border:1px solid var(--line);background:var(--bg);padding:0 32px 0 14px;
  font-size:14px;cursor:pointer;appearance:none;-webkit-appearance:none;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2371717A' stroke-width='2.5' stroke-linecap='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
  background-repeat:no-repeat;background-position:right 12px center}
select:hover{border-color:var(--line-strong)}
.chip{display:inline-flex;align-items:center;gap:6px;height:36px;padding:0 14px;border-radius:999px;flex:none;
  border:1px solid var(--line);background:var(--bg);color:var(--ink-2);font-size:14px;cursor:pointer;
  transition:background var(--t1) var(--ease),border-color var(--t1) var(--ease),color var(--t1) var(--ease)}
.chip:hover{border-color:var(--line-strong);color:var(--ink)}
.chip.on{background:var(--accent-soft);border-color:var(--accent);color:var(--accent)}
.chip small{font-size:12px;color:var(--ink-3)}
.chip.on small{color:var(--accent)}
.total{font-size:14px;color:var(--ink-2);white-space:nowrap}
.total b{color:var(--ink);font-weight:600}

/* === ENCARGO: los filtros, desplegados bajo la barra === */
.panel{background:var(--surface);border-bottom:1px solid var(--line)}
.panel-in{display:grid;gap:32px 40px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));padding-top:32px;padding-bottom:32px}
.grupo{display:flex;flex-direction:column;gap:12px;min-width:0}
.grupo+.grupo{min-width:0}
.fichas{display:flex;flex-wrap:wrap;gap:6px}
.panel .chip{height:32px;font-size:13px;padding:0 12px}
.par{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.tres{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.campo{display:flex;flex-direction:column;gap:6px;font-size:13px;color:var(--ink-2)}
.campo input{height:40px;border-radius:8px;border:1px solid var(--line-strong);
  background:var(--bg);padding:0 12px;font-size:14px;width:100%}
.campo input:focus,#excluir:focus{border-color:var(--accent);outline:none}
#excluir{height:40px;border-radius:8px;border:1px solid var(--line-strong);background:var(--bg);padding:0 12px;font-size:14px;width:100%}
.puerta{display:flex;gap:8px;align-items:center;flex-wrap:wrap;font-size:14px;color:var(--ink-2)}
.puerta input[type=number]{width:80px;height:36px;border-radius:8px;border:1px solid var(--line-strong);background:var(--bg);padding:0 10px}
input[type=checkbox]{width:18px;height:18px;accent-color:var(--accent);margin:0}
.ayuda{font-size:13px;color:var(--ink-3);margin:0;line-height:1.45}
.acc{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.acc select{flex:1 1 150px}

/* busqueda en los portales que no se pueden leer */
.fuera{display:flex;gap:6px 14px;flex-wrap:wrap;align-items:baseline;padding-top:20px;font-size:13px;color:var(--ink-3)}
.fuera:empty{display:none}
.fuera a{color:var(--ink-2);text-decoration:underline;text-decoration-color:var(--line-strong);text-underline-offset:3px}
.fuera a:hover{color:var(--accent);text-decoration-color:var(--accent)}

/* === RETICULA === */
.rejilla{display:grid;gap:40px 24px;padding-top:28px;padding-bottom:48px;
  grid-template-columns:repeat(auto-fill,minmax(var(--ancho),1fr))}
.ficha{display:flex;flex-direction:column;gap:12px;cursor:pointer;min-width:0}
.ficha:focus-visible{outline-offset:6px}
.lienzo{aspect-ratio:4/5;background:var(--surface);position:relative;overflow:hidden}
.lienzo img{width:100%;height:100%;object-fit:cover;display:block;transition:transform var(--t3) var(--ease)}
.ficha:hover .lienzo img{transform:scale(1.02)}
.novale{display:flex;align-items:center;justify-content:center;height:100%;font-size:13px;color:var(--ink-3)}
.like{position:absolute;top:10px;right:10px;width:40px;height:40px;border-radius:50%;border:0;
  display:flex;align-items:center;justify-content:center;background:var(--bg);color:var(--ink);cursor:pointer;
  box-shadow:0 1px 3px rgba(10,10,11,.12);transition:transform var(--t1) var(--ease),color var(--t1) var(--ease)}
.like:hover{transform:scale(1.06)}
.like.on{color:var(--accent)}
.like.on .ico{fill:currentColor}
.cartela{display:flex;flex-direction:column;gap:4px;min-width:0}
.origen{font-size:13px;color:var(--ink-3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.origen b{font-weight:600;color:var(--ink)}
.nombre{font-size:15px;font-weight:500;line-height:1.35;display:-webkit-box;-webkit-line-clamp:2;
  -webkit-box-orient:vertical;overflow:hidden;text-wrap:pretty}
.datos{font-size:13px;color:var(--ink-2);line-height:1.45}
.precio{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;margin-top:4px}
.precio b{font-size:17px;font-weight:600;letter-spacing:-.01em}
.precio s{font-size:13px;color:var(--ink-3)}
.precio span{font-size:13px;color:var(--ink-2)}

/* === DETALLE === */
.velo{position:fixed;inset:0;z-index:60;background:var(--scrim);display:flex;align-items:center;justify-content:center;padding:32px}
.hoja{position:relative;background:var(--bg);max-width:1200px;width:100%;max-height:92vh;overflow:auto;
  display:grid;grid-template-columns:1.25fr .75fr;box-shadow:var(--floating)}
.hoja .foto{background:var(--surface);display:flex;align-items:center;justify-content:center;min-height:360px;padding:32px}
.hoja .foto img{max-width:100%;max-height:80vh;object-fit:contain}
.hoja .info{padding:40px 32px 32px;display:flex;flex-direction:column;gap:20px;min-width:0}
.hoja h2{font-size:22px;line-height:1.25;margin:0;font-weight:600;letter-spacing:-.01em;text-wrap:balance;padding-right:40px}
.hoja .precio b{font-size:26px}
.hoja .desc{font-size:14px;line-height:1.55;color:var(--ink-2);margin:0;max-height:10em;overflow:auto;max-width:62ch}
dl{margin:0;display:grid;grid-template-columns:auto 1fr;gap:10px 24px;font-size:14px;border-top:1px solid var(--line);padding-top:20px}
dt{color:var(--ink-3)}
dd{margin:0;min-width:0;overflow-wrap:anywhere}
.notas{margin:0;padding:0;list-style:none;font-size:13px;color:var(--ink-2);display:flex;flex-direction:column;gap:6px}
.notas li::before{content:"";display:inline-block;width:5px;height:5px;border-radius:50%;background:var(--ink-3);margin:0 10px 2px 0}
.hoja .acc{margin-top:auto;padding-top:20px;border-top:1px solid var(--line)}
.icono{width:40px;height:40px;padding:0;display:inline-flex;align-items:center;justify-content:center;border-radius:50%;
  border:1px solid var(--line-strong);background:var(--bg);color:var(--ink);cursor:pointer;transition:background var(--t1) var(--ease)}
.icono:hover{background:var(--surface)}
.cerrar{position:absolute;top:16px;right:16px;z-index:2}
.paso{position:fixed;top:50%;transform:translateY(-50%);z-index:61}
.paso.izq{left:16px} .paso.der{right:16px}
.boton.me-gusta.on{background:var(--accent-soft);color:var(--accent)}
.boton.me-gusta.on .ico{fill:currentColor}

/* === VACIO, CARGAR MAS, PIE === */
.nada{padding:96px 24px;text-align:center}
.ballena-grande{display:block;width:180px;margin:0 auto 24px;color:var(--ink);--hueco:var(--bg);--acento:var(--accent)}
.nada p{margin:8px auto 0;max-width:42ch;color:var(--ink-2)}
.nada b{font-size:17px;font-weight:600}
.mas{display:flex;margin:0 auto 64px}
.pie{border-top:1px solid var(--line)}
.pie .envoltura{padding-top:24px;padding-bottom:40px;font-size:12px;color:var(--ink-3);line-height:1.6}

/* === RESPONSIVE === */
@media(max-width:900px){ .hoja{grid-template-columns:1fr;max-height:90vh}
  .hoja .foto{min-height:0} .hoja .foto img{max-height:50vh} .paso{display:none} }
@media(max-width:640px){ :root{--ancho:150px}
  .envoltura{padding:0 16px}
  /* en el movil la barra no se queda pegada: con dos filas tapaba la tercera parte de la pantalla */
  .barra{position:static}
  .fila1{height:auto;flex-wrap:wrap;gap:10px;padding:12px 16px}
  .marca{font-size:16px} .marca .ballena{width:36px}
  .buscador{order:3;flex-basis:100%;max-width:none}
  .acciones-barra{margin-left:auto} .acciones-barra .txt{display:none}
  .acciones-barra{flex-wrap:nowrap;gap:2px} .acciones-barra .total{display:none} .acciones-barra select{max-width:132px}
  .rejilla{gap:28px 12px;padding-top:20px}
  .like{width:34px;height:34px;top:8px;right:8px}
  .velo{padding:0} .hoja{max-height:100vh;height:100%} }
@media (prefers-reduced-motion:reduce){ *,*::before,*::after{transition-duration:0s!important;animation-duration:0s!important} }
</style></head><body>

<header class="barra">
  <div class="envoltura fila1">
    <h1 class="marca"><span class="ballena" aria-hidden="true">__BALLENA__</span>Caxi-Vaxi</h1>
    <div class="buscador"><svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
      <input id="q" type="search" aria-label="Buscar" placeholder="Buscar" autocomplete="off"></div>
    <div class="acciones-barra">
      <button id="abrir" class="boton borde" aria-expanded="false" aria-controls="panel"><svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M20 18h0"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/></svg><span class="txt">Filtros</span><span class="n" id="nfiltros" hidden></span></button>
      <span class="total"><b id="num">0</b> piezas</span>
      <select id="orden" aria-label="Ordenar">
        <option value="rel">Relevancia</option><option value="nuevo">Novedades</option>
        <option value="pa">Precio: menor a mayor</option><option value="pd">Precio: mayor a menor</option>
      </select>
      <button id="favoritos" class="boton" aria-pressed="false"><svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg><span class="txt">Favoritos</span></button>
      <button id="densidad" class="boton" data-d="1" aria-label="Tamaño de las fichas" title="Tamaño de las fichas"><svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg></button>
    </div>
  </div>
</header>

<section class="panel" id="panel" hidden><div class="envoltura">
  <div class="panel-in">
    <div class="grupo ancho">
      <span class="etq">Portal</span>
      <div class="fichas" id="portales" role="group" aria-label="Portal"></div>
    </div>
    <div class="grupo ancho">
      <span class="etq">Ubicaci&oacute;n</span>
      <div class="fichas" id="paises" role="group" aria-label="Ubicación"></div>
    </div>
    <div class="grupo">
      <span class="etq">Qu&eacute; busco</span>
      <div class="fichas" id="tipos"></div>
    </div>
    <div class="grupo">
      <span class="etq">Precio</span>
      <div class="par">
        <label class="campo">M&iacute;nimo<input type="number" id="pmin" placeholder="0 €" min="0" step="25"></label>
        <label class="campo">M&aacute;ximo<input type="number" id="tope" placeholder="Sin tope" min="0" step="25"></label>
      </div>
      <label class="puerta"><input type="checkbox" id="rebajas"> Solo rebajados</label>
    </div>
    <div class="grupo">
      <span class="etq">Medidas m&aacute;ximas, en cm</span>
      <div class="tres">
        <label class="campo">Ancho<input type="number" id="wmax" placeholder="220" min="0" step="5"></label>
        <label class="campo">Alto<input type="number" id="hmax" placeholder="200" min="0" step="5"></label>
        <label class="campo">Fondo<input type="number" id="dmax" placeholder="70" min="0" step="5"></label>
      </div>
      <label class="puerta"><input type="checkbox" id="puerta"> Que pase por una puerta de
        <input type="number" id="puertacm" value="200" min="50" step="5" aria-label="Ancho de la puerta en cm"> cm</label>
    </div>
    <div class="grupo">
      <span class="etq">Material</span>
      <div class="fichas" id="mats"></div>
    </div>
    <div class="grupo">
      <span class="etq">&Eacute;poca</span>
      <div class="fichas" id="epocas"></div>
      <span class="etq" style="margin-top:8px">Color</span>
      <div class="fichas" id="colores"></div>
    </div>
    <div class="grupo">
      <span class="etq">Excluir palabras</span>
      <input id="excluir" placeholder="dorado, tallado, ikea" aria-label="Palabras a excluir">
      <div class="acc">
        <button class="boton primario" id="aplicar">Ver resultados</button>
        <button class="boton borde" id="limpiar">Limpiar</button>
        <button class="boton borde" id="guardar">Guardar b&uacute;squeda</button>
        <select id="guardados" aria-label="Búsquedas guardadas"></select>
      </div>
    </div>
  </div>
  <div class="fuera" id="fuera"></div>
</div></section>

<main id="rejilla" class="envoltura rejilla" aria-label="Piezas encontradas"></main>
<button id="mas" class="boton borde mas" hidden>Cargar m&aacute;s</button>
<div id="nada" class="nada" hidden><span class="ballena-grande" aria-hidden="true">__BALLENA_CACHARROS__</span>
  <b>Nada por aqu&iacute;</b>
  <p>El cachalote baj&oacute; hasta el fondo y no encontr&oacute; nada parecido. Quita alg&uacute;n filtro.</p></div>
<div id="velo" class="velo" hidden></div>
<footer class="pie"><div class="envoltura">Caxi-Vaxi &middot; __TOTAL__ piezas le&iacute;das &middot; __FECHA__<br>
The term 'Etsy' is a trademark of Etsy, Inc. This Application uses Etsy's API, but is not endorsed or certified by Etsy.
eBay es una marca de eBay Inc. Esta aplicaci&oacute;n usa la API de eBay, pero no est&aacute; respaldada ni certificada por eBay.</div></footer>

<script>
const DATOS = __DATOS__;
/* Votos: ahora solo "me gusta". Se guarda con la misma clave de siempre; los
   votos viejos de "me gusta" (2) y "me encanta" (3) cuentan como me gusta. */
const K='cazalotes.votos', KE='cazalotes.encargos';
let votos={}, encargos={};
try{ votos=JSON.parse(localStorage.getItem(K)||'{}'); }catch(e){}
try{ encargos=JSON.parse(localStorage.getItem(KE)||'{}'); }catch(e){}
function guardarTodo(){ try{
  localStorage.setItem(K,JSON.stringify(votos));
  localStorage.setItem(KE,JSON.stringify(encargos)); }catch(e){} }
const gusta=id=>votos[id]==='3'||votos[id]==='2';
const $=s=>document.querySelector(s);
const ANCHOS=[200,280,380];
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,
  c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const eur=v=>v==null?'':Math.round(v).toLocaleString('es-ES')+' €';
/* Iconos Lucide en linea, un solo trazo: nada de emoji ni simbolos unicode */
const ICO={
  heart:'<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>',
  x:'<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
  izq:'<path d="m15 18-6-6 6-6"/>', der:'<path d="m9 18 6-6-6-6"/>',
  fuera:'<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>'
};
const ico=n=>'<svg class="ico" viewBox="0 0 24 24" aria-hidden="true">'+ICO[n]+'</svg>';
let visibles=[];

/* vocabulario del buscador: sinonimos reales de catalogo espanol */
const TIPOS={
 /* muebles de guardar en los idiomas en que escriben las fuentes: espanol,
    ingles (Etsy, 1stDibs, The Oblist), italiano, frances, aleman y neerlandes.
    Son expresiones regulares: van con limite de palabra por la izquierda.
    "bureau" NO: en frances y neerlandes es escritorio (lampe de bureau). */
 'almacenaje':['cajonera','cajonero','comoda','aparador','armario','alacena','ropero',
   'credenza','chifonier','chiffonn?ier','sinfonier','(?<!en |medidas |de )vitrin[ae](?!:)','taquillon',
   'trinchero','mueble bar','mueble bajo','sideboard','highboard','lowboard','dresser',
   'chests? of drawers','chest(?!erfield|nut)','commode','cabinet','cupboard','wardrobe',
   'armoire','tallboy','tansu','(?<!bernard )buffet','enfilade','bahut','semainier',
   'cassettiera','cassettone','armadio','madia','mobile bar','kommode','schrank','anrichte',
   'ladekast','dressoir'],
 'asiento':['silla','sillon','butaca','taburete','banqueta','sofa','canape','banco'],
 'mesa':['mesa','mesita','velador','escritorio','buro','mesa de centro','mesa de comedor'],
 'luz':['lampara','flexo','aplique','candelabro','farol','plafon','luminaria','quinque'],
 'escultura':['escultura','busto','talla','figura','relieve','estatua'],
 'pintura':['oleo','acuarela','pintura','lienzo','cuadro','gouache','temple'],
 'estanteria':['estanteria','libreria','balda','repisa'],
 'espejo':['espejo'],
 'alfombra':['alfombra','kilim','tapiz'],
 'ceramica':['ceramica','porcelana','jarron','loza','gres']
};
/* una expresion por tipo, compilada una vez. Limite de palabra por la
   izquierda: sin el, "chest" saltaba en "Manchester" y "mesa" en "remesa". */
/* El mueble siempre se nombra en el titulo. En la descripcion "armario" o
   "cabinet" aparecen en cuadros y en cuencos ("display cabinet"). */
const SOLO_TITULO=new Set(['almacenaje']);
/* Lo que nombra un mueble sin serlo: "Mid Century Dresser Jewelry Box",
   "Vanity Tray", "Miniature Tansu Chest". Se mira en el titulo. */
const TIPOS_NO={almacenaje:/jewel|joyer|trinket|tray|bandeja|perfum|figurin|glasses|goblet|decanter|organi[sz]er|runner|key ?box|catch-?all|miniatur|1:6|lint brush|money ?box|handles? for|dish|knob|pomo|tirador|pattern|art for|frame|interior with|accessor|essentials|pants|valet|jars?\b|vanity set|powder|vase|hanging|lundby|\bmini\b|kitchen design/};
/* y si declara medidas, un mueble de guardar mide al menos 35 cm por algun lado */
const TIPOS_MIN_CM={almacenaje:35};
const _reTipos={};
function reTipo(t){
  return _reTipos[t]||(_reTipos[t]=new RegExp('(?:^|[^a-z0-9])(?:'+(TIPOS[t]||['$^']).join('|')+')'));
}
const MATS=['roble','nogal','teca','palisandro','pino','haya','bronce','marmol',
            'hierro','acero','laton','ceramica','cristal','cuero','mimbre','formica'];
const EPOCAS=['1950','1960','1970','1980','s. XIX','s. XVIII'];
const COLS=['blanco','negro','gris','rojo','azul','verde','amarillo','naranja','marron','dorado','cromado'];
/* palabra con la que se busca cada tipo en las webs de fuera */
const PRINCIPAL={almacenaje:'comoda',asiento:'silla',mesa:'mesa',luz:'lampara',
  escultura:'escultura',pintura:'cuadro',estanteria:'estanteria',espejo:'espejo',
  alfombra:'alfombra',ceramica:'ceramica'};

/* Sin tildes y en minusculas: el catalogo escribe "Cómoda" y el vocabulario
   "comoda". Sin normalizar, la mitad de las busquedas fallaban en silencio. */
const plano=s=>String(s||'').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'');
DATOS.forEach(d=>{
  d._t=plano(d.titulo+' '+(d.desc||'')+' '+(d.mats||[]).join(' ')+' '+d.fuente);
  d._tt=plano(d.titulo+' '+(d.desc||'').slice(0,160));
  d._ti=plano(d.titulo);
});

const ETIQ={'1950':'Años 50','1960':'Años 60','1970':'Años 70','1980':'Años 80','s. XIX':'Siglo XIX','s. XVIII':'Siglo XVIII'};
function chips(cont,lista){
  $(cont).innerHTML=lista.map(x=>'<button class="chip" data-x="'+esc(x)+'" aria-pressed="false">'+esc(ETIQ[x]||x)+'</button>').join('');
}
chips('#tipos',Object.keys(TIPOS)); chips('#mats',MATS); chips('#epocas',EPOCAS);
chips('#colores',COLS);
const marcados=cont=>[...document.querySelectorAll(cont+' .chip.on')].map(c=>c.dataset.x);

/* eBay: su licencia prohibe mezclar sus anuncios con los de otras fuentes y
   mostrarlos con mas de 6 h desde la consulta. Solo aparecen eligiendo "eBay"
   en el desplegable, solos, y con la hora de la consulta a la vista. */
const EBAY='eBay', EBAY_MAX_H=6;
const horasDesde=iso=>(Date.now()-Date.parse(iso))/36e5;
const caducado=d=>d.aparte&&(!d.obt||horasDesde(d.obt)>EBAY_MAX_H);
function haceTxt(iso){ const h=horasDesde(iso);
  return h<1?'hace '+Math.max(1,Math.round(h*60))+' min':'hace '+h.toFixed(1).replace('.',',')+' h'; }

/* Portales: todos por defecto; se pueden elegir varios. eBay va solo (licencia). */
const cuentaPortal={}; DATOS.forEach(d=>{ if(!caducado(d)){ const g=d.grupo||d.fuente; cuentaPortal[g]=(cuentaPortal[g]||0)+1; } });
$('#portales').innerHTML='<button class="chip on" data-portal="" aria-pressed="true">Todos</button>'
  +Object.keys(cuentaPortal).sort((a,b)=>cuentaPortal[b]-cuentaPortal[a])
    .map(f=>'<button class="chip" data-portal="'+esc(f)+'" aria-pressed="false">'+esc(f===EBAY?'eBay (aparte)':f)
      +' <small>'+cuentaPortal[f].toLocaleString('es-ES')+'</small></button>').join('');
const portalesMarcados=()=>[...document.querySelectorAll('#portales .chip.on')].map(c=>c.dataset.portal).filter(Boolean);
function marcarPortal(c){
  const todos=[...document.querySelectorAll('#portales .chip')];
  const pon=(x,on)=>{ x.classList.toggle('on',on); x.setAttribute('aria-pressed',String(on)); };
  if(!c.dataset.portal){ todos.forEach(x=>pon(x,!x.dataset.portal)); return; }
  pon(c,!c.classList.contains('on'));
  /* eBay no se mezcla con nada: elegirlo apaga los demas, y al reves */
  if(c.classList.contains('on'))todos.forEach(x=>{ if(x!==c&&x.dataset.portal&&((c.dataset.portal===EBAY)||(x.dataset.portal===EBAY)))pon(x,false); });
  pon(todos[0],!portalesMarcados().length);
}

/* Paises: "Europa" es todo; los demas, los que tienen piezas, de mas a menos.
   Una pieza sin pais conocido sale en Europa pero no al elegir un pais. */
const NOMBRE_PAIS={};
DATOS.forEach(d=>{ if(d.pais&&d.lugar) NOMBRE_PAIS[d.pais]=d.lugar.split(', ').pop(); });
const cuentaPais={}; DATOS.forEach(d=>{ if(d.pais) cuentaPais[d.pais]=(cuentaPais[d.pais]||0)+1; });
const ordenPaises=Object.keys(cuentaPais).sort((a,b)=>cuentaPais[b]-cuentaPais[a]);
$('#paises').innerHTML='<button class="chip on" data-pais="" aria-pressed="true">Europa</button>'
  +ordenPaises.map(p=>'<button class="chip" data-pais="'+p+'" aria-pressed="false">'+esc(NOMBRE_PAIS[p]||p)
    +' <small>'+cuentaPais[p].toLocaleString('es-ES')+'</small></button>').join('');
const paisesMarcados=()=>[...document.querySelectorAll('#paises .chip.on')].map(c=>c.dataset.pais).filter(Boolean);
function marcarPais(c){
  const todos=document.querySelectorAll('#paises .chip');
  if(!c.dataset.pais){ todos.forEach(x=>{ x.classList.toggle('on',!x.dataset.pais); x.setAttribute('aria-pressed',String(!x.dataset.pais)); }); }
  else{ c.classList.toggle('on'); c.setAttribute('aria-pressed',String(c.classList.contains('on')));
    const hay=paisesMarcados().length; const eu=document.querySelector('#paises .chip[data-pais=""]');
    eu.classList.toggle('on',!hay); eu.setAttribute('aria-pressed',String(!hay)); }
}

document.addEventListener('click',e=>{
  const c=e.target.closest('.chip'); if(!c)return;
  if(c.closest('#paises')){ marcarPais(c); pintar(); return; }
  if(c.closest('#portales')){ marcarPortal(c); pintar(); return; }
  c.classList.toggle('on'); c.setAttribute('aria-pressed',String(c.classList.contains('on')));
  contarFiltros();
});

/* "Años 60 · 190 x 42 x 78 cm · teca, palisandro": solo lo que se sabe */
function datosPieza(d){
  return [d.ano,d.dims,(d.mats||[]).slice(0,3).join(', ')].filter(Boolean).map(esc).join(' · ');
}
function origen(d){
  const portal=esc(d.grupo||d.fuente);
  const extra=d.aparte?'consultado '+haceTxt(d.obt):(d.lugar||'');
  return '<b>'+portal+'</b>'+(extra?' · '+esc(extra):'');
}
function lineaPrecio(d){
  if(d.salida==null)return '';
  return '<div class="precio"><b>'+eur(d.salida)+'</b>'
    +(d.antes?'<s>'+eur(d.antes)+'</s>':'')
    +(d.envio===0?'<span>Envío gratis</span>':(d.envio?'<span>Envío '+eur(d.envio)+'</span>':''))
    +(!d.fijo?'<span>salida</span>':'')+'</div>';
}

function ficha(d,i){
  const g=gusta(d.id);
  const img=d.img
    ? '<img loading="lazy" src="'+esc(d.img)+'" alt="'+esc(d.titulo)+'">'
    : '<div class="novale">Sin fotografía</div>';
  const dat=datosPieza(d);
  return '<article class="ficha" data-i="'+i+'" tabindex="0">'
    +'<div class="lienzo">'+img
    +'<button class="like'+(g?' on':'')+'" data-id="'+esc(d.id)+'" aria-pressed="'+g+'" aria-label="Me gusta">'+ico('heart')+'</button></div>'
    +'<div class="cartela">'
    +'<div class="origen">'+origen(d)+'</div>'
    +'<div class="nombre">'+esc(d.titulo)+'</div>'
    +(dat?'<div class="datos">'+dat+'</div>':'')
    +lineaPrecio(d)
    +'</div></article>';
}

function leerEncargo(){
  return {
    q:plano($('#q').value).trim(),
    fuentes:portalesMarcados(), orden:$('#orden').value,
    tipos:marcados('#tipos'), mats:marcados('#mats'), epocas:marcados('#epocas'),
    cols:marcados('#colores'), paises:paisesMarcados(),
    wmax:+$('#wmax').value||0, hmax:+$('#hmax').value||0, dmax:+$('#dmax').value||0,
    puerta:$('#puerta').checked?(+$('#puertacm').value||0):0,
    pmin:+$('#pmin').value||0, tope:+$('#tope').value||0,
    rebajas:$('#rebajas').checked,
    excluir:plano($('#excluir').value).split(',').map(s=>s.trim()).filter(Boolean),
    fav:$('#favoritos').classList.contains('on')
  };
}

function cumple(d,E){
  /* texto libre: todas las palabras tienen que aparecer, en cualquier orden */
  if(E.q&&!E.q.split(/\s+/).every(w=>d._t.includes(w)))return false;
  if(E.fuentes.length&&!E.fuentes.includes(d.grupo||d.fuente))return false;
  if(d.aparte&&(E.fuentes.join()!==EBAY||caducado(d)))return false;
  if(E.paises.length&&!E.paises.includes(d.pais))return false;
  if(E.fav&&!gusta(d.id))return false;
  if(E.excluir.some(x=>d._t.includes(x)))return false;
  if(E.tipos.length){
    /* el tipo se busca en el titulo y el arranque de la descripcion, no en
       todo el texto: asi "mesa" no cuela un cuadro que menciona una mesa */
    if(!E.tipos.some(t=>reTipo(t).test(SOLO_TITULO.has(t)?d._ti:d._tt)
        &&!(TIPOS_NO[t]&&TIPOS_NO[t].test(d._ti))
        &&!(TIPOS_MIN_CM[t]&&d.d3&&d.d3.length&&Math.max(...d.d3)<TIPOS_MIN_CM[t])))return false;
  }
  if((E.cols||[]).length&&!E.cols.some(c=>(d.col||[]).includes(c)))return false;
  if(E.mats.length&&!E.mats.some(m=>(d.mats||[]).includes(m)))return false;
  if(E.epocas.length&&!E.epocas.includes(d.periodo))return false;
  const precio=d.total!=null?d.total:d.salida;
  if(E.tope&&precio!=null&&precio>E.tope)return false;
  if(E.pmin&&(precio==null||precio<E.pmin))return false;
  if(E.rebajas&&!d.antes)return false;
  /* medidas: duras SOLO si la pieza las declara. Sin medidas no se descarta. */
  if(d.d3&&d.d3.length){
    const o=[...d.d3].sort((a,b)=>b-a);
    if(E.wmax&&o[0]>E.wmax)return false;
    if(E.hmax&&o.length>1&&o[1]>E.hmax)return false;
    if(E.dmax&&o.length>2&&o[2]>E.dmax)return false;
    if(E.puerta&&o.length>1&&Math.min(o[0],o[1])>E.puerta)return false;
  }
  return true;
}

const ORDEN={
  rel:(a,b)=>b.g-a.g,
  nuevo:(a,b)=>String(b.alta||'').localeCompare(String(a.alta||'')),
  pa:(a,b)=>(a.salida==null?1e9:a.salida)-(b.salida==null?1e9:b.salida),
  pd:(a,b)=>(b.salida==null?-1:b.salida)-(a.salida==null?-1:a.salida)
};
function pintar(){
  const E=leerEncargo();
  visibles=DATOS.filter(d=>cumple(d,E)).sort(ORDEN[E.orden]||ORDEN.rel);
  $('#rejilla').innerHTML=''; pintados=0; pintarMas();
  $('#nada').hidden=visibles.length>0;
  $('#num').textContent=visibles.length.toLocaleString('es-ES');
  contarFiltros(); enlacesFuera(E);
}

/* Cuantos filtros del encargo estan puestos: se ve en el boton aunque el
   panel este cerrado */
function contarFiltros(){
  const E=leerEncargo();
  const n=E.fuentes.length+E.paises.length+E.tipos.length+E.mats.length+E.epocas.length+E.cols.length+E.excluir.length
    +(E.wmax?1:0)+(E.hmax?1:0)+(E.dmax?1:0)+(E.puerta?1:0)+(E.pmin?1:0)+(E.tope?1:0)+(E.rebajas?1:0);
  $('#nfiltros').hidden=!n; $('#nfiltros').textContent=n;
}

/* Se pintan de 60 en 60 y el resto llega solo al bajar: scroll infinito */
let pintados=0; const TANDA=60;
function pintarMas(){
  const trozo=visibles.slice(pintados,pintados+TANDA);
  $('#rejilla').insertAdjacentHTML('beforeend',trozo.map((d,j)=>ficha(d,pintados+j)).join(''));
  pintados+=trozo.length;
  $('#mas').hidden=pintados>=visibles.length;
}

/* Portales cuyo buscador no se puede leer: se abren con la busqueda puesta */
function enlacesFuera(E){
  const partes=[];
  if(E.q)partes.push(E.q);
  else if(E.tipos.length)partes.push(PRINCIPAL[E.tipos[0]]||E.tipos[0]);
  if((E.cols||[]).length){
    const c=E.cols[0]; partes.push(partes[0]&&/a$/.test(partes[0])&&/o$/.test(c)?c.slice(0,-1)+'a':c); }
  if(E.mats.length)partes.push(E.mats[0]);
  const consulta=partes.join(' ').trim();
  const caja=$('#fuera');
  if(!consulta){ caja.innerHTML=''; return; }
  const q=encodeURIComponent(consulta), t=E.tope||'';
  const sitios=[
    /* Catawiki: Akamai bloquea cualquier lectura automatica, robots.txt incluido */
    ['Catawiki','https://www.catawiki.com/es/s?q='+q+(t?'&max_price='+t:'')],
    ['Wallapop','https://es.wallapop.com/search?keywords='+q+(t?'&max_sale_price='+t:'')+'&order_by=newest'],
    ['Milanuncios','https://www.milanuncios.com/anuncios/?s='+q+(t?'&hasta='+t:'')],
    ['eBay','https://www.ebay.es/sch/i.html?_nkw='+q+(t?'&_udhi='+t:'')],
    ['Etsy','https://www.etsy.com/es/search?q='+q+(t?'&max='+t:'')],
    ['Vinted','https://www.vinted.es/catalog?search_text='+q+(t?'&price_to='+t:'')],
    ['Pamono','https://www.pamono.es/catalogsearch/result/?q='+q],
    ['1stDibs','https://www.1stdibs.com/search/?q='+q],
    ['The Oblist','https://oblist.com/search?q='+q]
  ];
  caja.innerHTML='<span>Buscar «'+esc(consulta)+'» directamente en</span>'
    +sitios.map(s=>'<a href="'+s[1]+'" target="_blank" rel="noopener">'+s[0]+'</a>').join('');
}

let actual=-1;
function detalle(i){
  actual=i; const d=visibles[i]; if(!d)return;
  const g=gusta(d.id);
  const filas=[['Portal',d.fuente],
    ['Consultado',d.aparte?haceTxt(d.obt)+' (en eBay puede haber cambiado)':null],
    ['Ubicación',d.lugar],['Año',d.ano],['Medidas',d.dims],
    ['Materiales',(d.mats||[]).join(', ')],
    ['Envío',d.envio===0?'Gratis':(d.envio?eur(d.envio):null)],
    ['Con comisión',(!d.fijo&&d.total&&Math.round(d.total)!==Math.round(d.salida))?eur(d.total):null],
    ['Precio original',d.orig&&!/ EUR$/.test(d.orig)?d.orig:null],
    ['Lote',d.lote&&!d.fijo?d.lote:null]]
    .filter(p=>p[1]).map(p=>'<dt>'+esc(p[0])+'</dt><dd>'+esc(p[1])+'</dd>').join('');
  const notas=(d.avisos||[]).map(a=>'<li>'+esc(a)+'</li>').join('');
  $('#velo').innerHTML='<div class="hoja" role="dialog" aria-modal="true" aria-label="'
    +esc(d.titulo)+'" tabindex="-1">'
    +'<div class="foto">'+(d.img?'<img src="'+esc(d.imgG||d.img)+'" data-chica="'+esc(d.img)
        +'" onerror="if(this.src!==this.dataset.chica)this.src=this.dataset.chica" alt="'+esc(d.titulo)+'">'
        :'<div class="novale">Sin fotografía</div>')+'</div>'
    +'<div class="info">'
    +'<button class="icono cerrar" id="x" aria-label="Cerrar">'+ico('x')+'</button>'
    +'<div class="origen">'+origen(d)+'</div>'
    +'<h2>'+esc(d.titulo)+'</h2>'
    +lineaPrecio(d)
    +(d.desc?'<p class="desc">'+esc(d.desc)+'</p>':'')
    +(filas?'<dl>'+filas+'</dl>':'')
    +(notas?'<ul class="notas">'+notas+'</ul>':'')
    +'<div class="acc">'
    +'<a class="boton primario" href="'+esc(d.url)+'" target="_blank" rel="noopener">'+ico('fuera')+'Ver en '+esc(d.grupo||d.fuente)+'</a>'
    +'<button class="boton borde me-gusta'+(g?' on':'')+'" data-id="'+esc(d.id)+'" aria-pressed="'+g+'">'+ico('heart')+'Me gusta</button>'
    +'</div></div></div>'
    +'<button class="icono paso izq" id="ant" aria-label="Anterior">'+ico('izq')+'</button>'
    +'<button class="icono paso der" id="des" aria-label="Siguiente">'+ico('der')+'</button>';
  $('#velo').hidden=false; document.body.style.overflow='hidden';
  const h=$('.hoja'); if(h) h.focus();
}
function cerrar(){ $('#velo').hidden=true; document.body.style.overflow=''; actual=-1; }
function mover(n){ const i=actual+n; if(i>=0&&i<visibles.length)detalle(i); }

document.addEventListener('click',function(e){
  const bl=e.target.closest('.like,.me-gusta');
  if(bl){ e.stopPropagation();
    const id=bl.dataset.id;
    if(gusta(id)) delete votos[id]; else votos[id]='3';
    guardarTodo();
    /* se actualiza en el sitio: repintar todo te devolveria al principio */
    document.querySelectorAll('.like,.me-gusta').forEach(b=>{
      if(b.dataset.id===id){ b.classList.toggle('on',gusta(id)); b.setAttribute('aria-pressed',String(gusta(id))); } });
    return; }
  if(e.target.closest('#mas')){ pintarMas(); return; }
  if(e.target.closest('#x')||e.target.id==='velo'){ cerrar(); return; }
  if(e.target.closest('#des')){ mover(1); return; }
  if(e.target.closest('#ant')){ mover(-1); return; }
  const f=e.target.closest('.ficha');
  if(f&&!e.target.closest('a')) detalle(+f.dataset.i);
});
document.addEventListener('keydown',function(e){
  if($('#velo').hidden){
    if(e.key==='Enter'&&document.activeElement&&document.activeElement.classList.contains('ficha'))
      detalle(+document.activeElement.dataset.i);
    return; }
  if(e.key==='Escape')cerrar();
  if(e.key==='ArrowRight')mover(1);
  if(e.key==='ArrowLeft')mover(-1);
});

$('#abrir').addEventListener('click',e=>{
  const p=$('#panel'); p.hidden=!p.hidden;
  e.currentTarget.classList.toggle('on',!p.hidden);
  e.currentTarget.setAttribute('aria-expanded',String(!p.hidden)); });
$('#favoritos').addEventListener('click',e=>{
  const b=e.currentTarget; b.classList.toggle('on'); b.setAttribute('aria-pressed',String(b.classList.contains('on'))); pintar(); });
/* el buscador filtra mientras escribes, con una pausa corta */
let espera; $('#q').addEventListener('input',()=>{ clearTimeout(espera); espera=setTimeout(pintar,140); });
$('#orden').addEventListener('change',pintar);
$('#aplicar').addEventListener('click',()=>{ pintar(); window.scrollTo({top:0}); });
$('#rebajas').addEventListener('change',contarFiltros);
/* Enter en cualquier campo del panel lanza la busqueda */
$('#panel').addEventListener('keydown',e=>{ if(e.key==='Enter'&&e.target.tagName==='INPUT')pintar(); });
$('#panel').addEventListener('input',contarFiltros);
if('IntersectionObserver' in window){
  new IntersectionObserver(es=>{ if(es[0].isIntersecting&&!$('#mas').hidden)pintarMas(); },
    {rootMargin:'800px'}).observe($('#mas'));
}
$('#limpiar').addEventListener('click',()=>{
  ['wmax','hmax','dmax','tope','pmin','excluir','q'].forEach(id=>$('#'+id).value='');
  $('#puerta').checked=false; $('#rebajas').checked=false;
  document.querySelectorAll('#panel .chip.on').forEach(c=>{ c.classList.remove('on'); c.setAttribute('aria-pressed','false'); });
  pintar(); });
$('#densidad').addEventListener('click',e=>{
  const n=(+e.currentTarget.dataset.d+1)%3; e.currentTarget.dataset.d=n;
  document.documentElement.style.setProperty('--ancho',ANCHOS[n]+'px');
  try{ localStorage.setItem('cazalotes.ancho',n); }catch(err){} });
try{ const n=+localStorage.getItem('cazalotes.ancho');
  if(n>=0&&n<3&&localStorage.getItem('cazalotes.ancho')!==null){ $('#densidad').dataset.d=n;
    document.documentElement.style.setProperty('--ancho',ANCHOS[n]+'px'); } }catch(e){}

/* encargos guardados */
function pintarGuardados(){
  $('#guardados').innerHTML='<option value="">Búsquedas guardadas</option>'
    +Object.keys(encargos).map(n=>'<option>'+esc(n)+'</option>').join(''); }
$('#guardar').addEventListener('click',()=>{
  const n=prompt('Nombre de la búsqueda'); if(!n)return;
  encargos[n]=leerEncargo(); guardarTodo(); pintarGuardados(); });
function ponerEncargo(E){
  $('#q').value=E.q||''; $('#orden').value=ORDEN[E.orden]?E.orden:'rel';
  $('#wmax').value=E.wmax||''; $('#hmax').value=E.hmax||''; $('#dmax').value=E.dmax||'';
  $('#tope').value=E.tope||''; $('#pmin').value=E.pmin||''; $('#excluir').value=(E.excluir||[]).join(', ');
  $('#puerta').checked=!!E.puerta; if(E.puerta)$('#puertacm').value=E.puerta;
  $('#rebajas').checked=!!E.rebajas;
  document.querySelectorAll('#panel .chip').forEach(c=>{ c.classList.remove('on'); c.setAttribute('aria-pressed','false'); });
  [['#tipos',E.tipos],['#mats',E.mats],['#epocas',E.epocas],['#colores',E.cols]].forEach(([sel,arr])=>
    (arr||[]).forEach(x=>{ const c=document.querySelector(sel+' .chip[data-x="'+x+'"]');
      if(c){ c.classList.add('on'); c.setAttribute('aria-pressed','true'); } }));
  marcarPortal(document.querySelector('#portales .chip[data-portal=""]'));
  (E.fuentes||(E.fuente?[E.fuente]:[])).forEach(f=>{ const c=[...document.querySelectorAll('#portales .chip')].find(x=>x.dataset.portal===f); if(c)marcarPortal(c); });
  const eu=document.querySelector('#paises .chip[data-pais=""]'); marcarPais(eu);
  (E.paises||[]).forEach(p=>{ const c=document.querySelector('#paises .chip[data-pais="'+p+'"]'); if(c)marcarPais(c); });
  pintar(); }
$('#guardados').addEventListener('change',e=>{
  const E=encargos[e.target.value]; if(E)ponerEncargo(E); });
pintarGuardados();

/* Una busqueda puede venir en el enlace, para abrir la pagina ya filtrada:
   vista.html#tipos=almacenaje&tope=   (tope vacio = sin tope de precio)
   Claves: q, fuente, orden, tipos, mats, epocas, cols, paises, pmin, tope,
   wmax, hmax, dmax, excluir. Las listas van separadas por comas. */
function encargoDelEnlace(){
  const h=new URLSearchParams(location.hash.slice(1)); if(![...h.keys()].length)return null;
  const lista=k=>(h.get(k)||'').split(',').map(x=>x.trim()).filter(Boolean);
  return {q:h.get('q')||'', fuentes:lista('fuentes').concat(h.get('fuente')?[h.get('fuente')]:[]), orden:h.get('orden')||'rel',
    tipos:lista('tipos'), mats:lista('mats'), epocas:lista('epocas'), cols:lista('cols'), paises:lista('paises'),
    pmin:+h.get('pmin')||'', tope:+h.get('tope')||'',
    wmax:+h.get('wmax')||'', hmax:+h.get('hmax')||'', dmax:+h.get('dmax')||'',
    excluir:lista('excluir')};
}
window.addEventListener('hashchange',()=>{ const E=encargoDelEnlace(); if(E)ponerEncargo(E); });

const delEnlace=encargoDelEnlace();
if(delEnlace)ponerEncargo(delEnlace); else pintar();
</script></body></html>
"""
