/*
 * Puerta de Caxi-Vaxi en Cloudflare Pages.
 *
 * La pagina es privada: todo pasa por aqui antes de servirse. Sin la cookie
 * de acceso se ensena solo el formulario de la clave. La clave vive como
 * secreto del proyecto (CLAVE), nunca en el repo. Si no hay clave
 * configurada, no se sirve nada (falla cerrada).
 *
 * Se eligio esto y no Cloudflare Access porque Access exige guardar una
 * tarjeta; asi la cuenta sigue sin metodo de pago y no se le puede cobrar.
 */

const COOKIE = "cv";
const DIAS = 180;

async function hmac(clave, texto) {
  const k = await crypto.subtle.importKey("raw", new TextEncoder().encode(clave),
    { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const f = await crypto.subtle.sign("HMAC", k, new TextEncoder().encode(texto));
  return [...new Uint8Array(f)].map(b => b.toString(16).padStart(2, "0")).join("");
}

/* Comparacion en tiempo constante: se comparan las firmas, no las claves */
async function igual(a, b, sal) {
  const [x, y] = await Promise.all([hmac(sal, a), hmac(sal, b)]);
  let d = 0;
  for (let i = 0; i < x.length; i++) d |= x.charCodeAt(i) ^ y.charCodeAt(i);
  return d === 0 && x.length === y.length;
}

const BALLENA = '<svg viewBox="0 0 128 64" aria-hidden="true"><path fill="currentColor" d="M8,24 Q8,14 18,14 L54,14 C70,14 82,19 93,28 L104,34 L117,24 Q122,22 121,27 L111,36 L121,45 Q122,50 117,48 L104,38 C91,45 77,49 60,49 L26,49 Q19,49 17,45 L13,42 Q8,39 8,32 Z"/><path fill="currentColor" d="M48,47 Q52,58 62,58 Q57,53 57,47 Z"/><g fill="none" stroke="var(--bg)" stroke-width="1.6" stroke-linecap="round"><path d="M15,42 L42,44"/><path d="M72,29 h9 M76,34 h9 M71,39 h8"/></g><circle cx="45" cy="34" r="2" fill="var(--bg)"/><g fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M13,11 L6,3"/><path d="M17,10 L15,1"/><path d="M10,13 L2,9"/></g></svg>';

function formulario(fallo) {
  const html = `<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Caxi-Vaxi</title>
<style>
:root{--bg:#FFFFFF;--surface:#F4F4F5;--line:#D4D4D8;--ink:#0A0A0B;--ink-2:#52525B;--accent:#1E3BFF;--on:#FFFFFF;color-scheme:light}
@media (prefers-color-scheme:dark){:root{--bg:#0B0B0D;--surface:#161618;--line:#34343B;--ink:#F4F4F5;--ink-2:#A1A1AA;--accent:#7286FF;--on:#0B0B0D;color-scheme:dark}}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;display:grid;place-items:center;background:var(--bg);color:var(--ink);
  font:400 16px/1.5 ui-sans-serif,-apple-system,BlinkMacSystemFont,"Instrument Sans",sans-serif;padding:24px}
form{width:100%;max-width:340px;display:flex;flex-direction:column;gap:14px}
.marca{display:flex;align-items:center;gap:12px;font-size:22px;font-weight:600;margin-bottom:8px}
.marca svg{width:56px;color:var(--ink)}
label{font-size:14px;color:var(--ink-2)}
input{height:48px;border-radius:12px;border:1px solid var(--line);background:var(--surface);color:var(--ink);
  padding:0 14px;font:inherit;caret-color:var(--accent)}
input:focus{outline:2px solid var(--accent);outline-offset:1px;background:var(--bg)}
button{height:48px;border:0;border-radius:999px;background:var(--accent);color:var(--on);font:inherit;font-weight:600;cursor:pointer}
.error{color:#C42B1C;font-size:14px;margin:0}
@media (prefers-color-scheme:dark){.error{color:#FF8A80}}
</style></head><body>
<form method="post" action="/entrar">
  <div class="marca">${BALLENA}Caxi-Vaxi</div>
  <label for="clave">Clave de acceso</label>
  <input id="clave" name="clave" type="password" autocomplete="current-password" required autofocus>
  ${fallo ? '<p class="error" role="alert">Esa clave no es. Prueba otra vez.</p>' : ""}
  <button type="submit">Entrar</button>
</form></body></html>`;
  return new Response(html, {
    status: 401,
    headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store",
      "X-Robots-Tag": "noindex, nofollow", "X-Frame-Options": "DENY" },
  });
}

export async function onRequest({ request, env, next }) {
  const clave = env.CLAVE;
  if (!clave) return new Response("Caxi-Vaxi no está configurada.", { status: 503 });

  const url = new URL(request.url);
  const ficha = await hmac(clave, "caxi-vaxi-v1");
  const galletas = (request.headers.get("Cookie") || "").split(/;\s*/);
  const dentro = galletas.includes(`${COOKIE}=${ficha}`);
  const fija = (valor, edad) =>
    `${COOKIE}=${valor}; Path=/; Max-Age=${edad}; Secure; HttpOnly; SameSite=Lax`;

  if (url.pathname === "/salir") {
    return new Response(null, { status: 303, headers: { Location: "/", "Set-Cookie": fija("", 0) } });
  }
  if (url.pathname === "/entrar" && request.method === "POST") {
    const datos = await request.formData();
    if (await igual(String(datos.get("clave") || ""), clave, ficha)) {
      return new Response(null, { status: 303,
        headers: { Location: "/", "Set-Cookie": fija(ficha, DIAS * 86400) } });
    }
    await new Promise(r => setTimeout(r, 900));   // frena a quien pruebe claves en bucle
    return formulario(true);
  }
  if (!dentro) return formulario(false);

  const r = await next();
  const h = new Headers(r.headers);
  h.set("X-Robots-Tag", "noindex, nofollow");
  h.set("Cache-Control", "private, no-cache");
  return new Response(r.body, { status: r.status, statusText: r.statusText, headers: h });
}
