# Auditoría de Caxi-Vaxi: UX/UI, diseño, legibilidad y SEO

13 de octubre de 2026. Herramientas: `impeccable` (audit técnico y detector automático), las guías
de accesibilidad WCAG 2.1 AA y la revisión de SEO. Página revisada: `datos/vista.html`, que genera
`plantilla.py`.

## Puntuación

| Dimensión | Antes | Después | Qué cambió |
|---|---|---|---|
| Accesibilidad | 2/4 | 3/4 | Estados `aria-pressed` en filtros y me gusta, foco visible en azul, contraste del texto terciario corregido (#71717A, 4,8:1) |
| Rendimiento | 3/4 | 3/4 | Tandas de 60 fichas con scroll infinito, imágenes en diferido; la página pesa por los 15.800 datos embebidos |
| Temas (claro/oscuro) | 3/4 | 4/4 | Todo con variables; modo oscuro propio, no invertido |
| Responsive | 2/4 | 3/4 | En el móvil la barra deja de quedarse fija y los países se deslizan en una sola fila |
| Coherencia del diseño | 2/4 | 3/4 | Una sola familia, un solo acento, cero datos de relleno en la ficha |
| **Total** | **12/20, aceptable** | **16/20, bien** | |

## Lo que fallaba y se arregló

**P0. La ficha hablaba de nosotros, no de la pieza.** Cuatro notas (gusto, oportunidad, logística,
confianza), avisos en rojo sobre «relleno para buscadores» y cinco botones de voto. Ahora la ficha
dice solo: portal, ubicación, título, año, medidas, materiales, precio y envío. Lo que no se sabe
no aparece.

**P1. No funcionaba como buscador.** El campo de texto estaba escondido entre ocho botones y el
placeholder era una lista de ejemplos. Ahora el buscador es el centro de la barra y dice «Buscar».
Debajo, el portal, los países y el orden, como en Pamono y 1stDibs.

**P1. No se sabía de dónde era cada pieza.** Cada ficha empieza con el portal en negrita y la ciudad
y el país.

**P1. Títulos en MAYÚSCULAS.** Muchos vendedores de Wallapop escriben así y en la rejilla se leía mal.
Se pasan a mayúscula inicial. Contrapartida: se pierde la mayúscula de algunos nombres propios
(«thonet»).

**P2. Ruido en la barra.** Fuera «sin vender», «solo nítidas», «ocultar descartados», «exportar
votos», la frase de la cabecera, el bloque de catálogo y fecha, y el aviso de fotos de baja
resolución. La fecha y el total pasan al pie.

**P2. Crema y naranja.** Se cambian por la paleta «Azul Klein»: blanco puro, grises fríos, tinta
casi negra y un azul eléctrico solo para lo que se toca y lo que te gusta.

**P2. Wallapop reservado.** Ya no aparece.

## Lo nuevo, sacado de Pamono y 1stDibs

- **Ubicación por países**, con «Europa» por defecto y el número de piezas de cada país. Lo que se
  sabe que está fuera de Europa no entra.
- **Precio mínimo y máximo** en lugar de un solo tope.
- **Solo rebajados**, cuando la tienda bajó el precio o Wallapop registró una bajada.
- **Orden por relevancia, novedades y precio** en las dos direcciones.
- **Favoritos**: un botón para ver solo lo que marcaste con me gusta.
- **Número de filtros activos** en el botón de Encargo, para saberlo con el panel cerrado.

## Lo que queda pendiente

- **[P1] País desconocido en el 58 % de las piezas.** 1stDibs, The Oblist y la mayoría de Pamono no
  publican la ubicación en las páginas que se pueden leer. Esas piezas salen en «Europa», pero no al
  elegir un país. En Pamono se puede sacar abriendo cada ficha (ya se hace con los muebles de
  guardar); en 1stDibs su robots.txt prohíbe abrir fichas.
- **[P2] Envío solo de eBay.** Wallapop, Etsy y las tiendas no dan el coste de envío en lo que
  leemos.
- **[P2] La relevancia sigue el perfil de gusto.** Las piezas de Wallapop con muchas palabras de
  estilo en la descripción suben demasiado. Es un ajuste de `puntuar.py`.
- **[P3] Fuente.** El detector marca Instrument Sans como muy usada. Se mantiene porque viene de
  Juddaun.

## SEO

No aplica de verdad: Caxi-Vaxi es una página local de uso personal, no está publicada y nadie la
busca en Google. Lo único que tiene sentido ya está hecho: título, descripción, idioma `es` y
`noindex, nofollow` por si algún día se sube a un servidor, para que no la indexen.
