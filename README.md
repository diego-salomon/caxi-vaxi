# Caxi-Vaxi

<img src="marca/cachalote_cacharros.svg" width="160" alt="A sperm whale spouting a desk lamp, a chair and a vase">

A personal tool for finding vintage furniture and art to put in my own flat in Madrid.

I collect mid-century furniture and Venezuelan naive art, and I was losing hours every week
opening the same auction catalogues one by one. This reads them for me and tells me which
lots are worth a look.

It is not a marketplace, a price comparison site, or a reselling tool. One user, me.

The name started as CazaLotes, "lot hunter", which sounds like *cachalote*, sperm whale.
Then it was Cacharrotes, from *cacharro*, what Venezuelans call any old thing. Now it is
Caxi-Vaxi: *cachivaches*, odds and ends, said the way *wabi-sabi* sounds, because the
things worth keeping are the old, worn and slightly imperfect ones. The repository keeps
the name caxi-vaxi too, on GitHub and on disk, since October 2026.

## What it does

**Reads catalogues.** Five Madrid auction houses (Durán, Sala Retiro, Segre, Ansorena,
Alcalá), three Shopify shops (La Basílica, Odalys, The Oblist), Pamono, 1stDibs, Etsy and
eBay through their APIs, and the Wallapop pages its `robots.txt` allows: single listings,
seller profiles and its themed landing pages.

**Scores them against my taste**, which lives in `perfil.py`: Shaker, Barragán, Donald Judd,
Vienna Secession, Danish teak, Venezuelan naive painters, sculpture and busts. And what I
don't want, which matters just as much: religious imagery, gilt carving, Louis XVI
reproductions.

**Reads the catalogue against me.** Spanish auction houses have a precise vocabulary that
most buyers miss. "Atribuido a" means the experts disagree. "Círculo de" means it is not by
the artist at all. "Firmado en plancha" means the signature is printed, not signed. The tool
flags those phrases, because they are where people overpay.

**Works out what it actually costs.** The hammer price is not the price. Each house has its
own buyer's premium (Segre 21.8%, Durán and Sala Retiro 23%, Alcalá 24.2%, Ansorena 25%
below €1,000), and some charge €6 a day in storage if you are slow to collect. The tool adds
all of it up before showing me anything.

**Takes a brief with hard limits.** `encargo.py` holds requests like "a chest of drawers no
wider than 220 cm, under €600, and it has to fit through a 200 cm door". Measurements are not
a preference, they are a constraint. A piece that does not fit is not an opportunity.

## What it deliberately does not do

**It does not bid.** Spanish auction conditions sell everything *cuerpo cierto*, as-is,
explicitly including errors of description, and you have 14 or 15 days to complain. The last
step is a human looking at the thing.

**It does not value anything.** Published research on vision models putting a name to a
painting reports accuracy between 6.7% and 12.6%. A tool that reads labels and stamps is
useful. One that tells you who painted something is lying to you.

**It does not scrape anything that asked not to be scraped.** The five auction houses publish
`robots.txt` files that allow everything. Wallapop forbids `/search` and any URL with a query
string, so its search is never touched, and neither is its internal search API, which only
answers clients pretending to be Chrome. What it reads are the pages `robots.txt` allows:
listings I saved, sellers I follow and a few themed landing pages. Etsy and eBay have
official APIs, which is why they are read with keys instead of worked around.

Everything runs without logging in. One request every three seconds, one pass a day, an
identifiable User-Agent with a real contact address, a full stop on any 403, and no
downloading of lot photographs: it stores the URL and links out.

## Running it

```bash
python3 -m venv .venv
.venv/bin/pip install beautifulsoup4 lxml requests
cp config.py config_local.py    # put your own contact address in it

.venv/bin/python run.py              # read the live catalogues, then rank
.venv/bin/python shopify.py          # La Basílica, Odalys and The Oblist
.venv/bin/python tiendas.py          # Pamono and 1stDibs
.venv/bin/python etsy.py             # Etsy, through its official API (needs keys, see below)
.venv/bin/python ebay.py             # eBay.es, through its official API (needs keys, see below)
.venv/bin/python wallapop.py         # Wallapop: saved listings, followed sellers, landing pages
.venv/bin/python vista.py            # build the page: datos/vista.html
open datos/vista.html                # browse, search, vote

.venv/bin/python run.py --informe    # re-rank what is already stored, in the terminal
.venv/bin/python run.py --historico  # also pull the past-sales archive (hours, do it once)
.venv/bin/python marketplaces.py     # build manual search links for sites with no API

.venv/bin/pip install pytest
.venv/bin/python -m pytest tests     # eBay and Wallapop readers, no network
```

## Etsy

Etsy is read through its official Open API v3, under a personal-access app approved on
2 October 2026. It needs two values in `config_local.py`, which is never committed:
`ETSY_KEYSTRING` and `ETSY_SHARED_SECRET`. Etsy requires both, joined by a colon, in the
`x-api-key` header.

Two of Etsy's API terms shape how this works. Content may not be shown more than 24 hours
older than on Etsy itself, and may not be stored longer than needed. So Etsy listings go to
`datos/etsy.json`, which is overwritten on every run and never accumulated, and the page
drops them automatically once they are more than 24 hours old. The page also carries the
trademark notice the terms require.

Each Etsy listing shows the original price and currency; the euro figure used for filtering
is an approximate conversion. Listings Etsy marks as recent are flagged as new rather than
vintage, and shops outside the EU are flagged for customs and import VAT.

Etsy sellers pad titles and the materials field with lists of designer names for search
("eames, rietveld, cadovius, le corbusier"). Titles are cut back to the part that describes
the piece, padded materials are dropped, and a listing that names four or more designers only
scores for the top two and is flagged. English catalogue vocabulary ("in the style of",
"replica", "attributed to") is flagged the way "estilo" and "atribuido a" are, ignoring the
harmless uses ("we never sell reproductions", "reproduction cloth cord"). Etsy's own size
fields are usually empty, so measurements are also read from labelled text in the
description ("height 81.5 cm, width 55 cm").

## eBay

eBay.es is read through the official Browse API, with an application token (client
credentials, no eBay login). It needs the App ID and Cert ID of a production keyset in
`config_local.py` as `EBAY_CLIENT_ID` and `EBAY_CLIENT_SECRET`. The searches are in Spanish,
capped at 900 €, for pieces located in Spain; `ebay.py --ue` widens that to the EU. Sizes
only come with the full listing, so the reader fetches those twenty at a time and reads
width, height and depth from eBay's item specifics, falling back to the description.

eBay's API License Agreement (read 13 October 2026) shapes four things:

- Listing data may not be shown more than six hours older than on eBay. `datos/ebay.json`
  is overwritten on every run, `vista.py` refuses it after six hours, and the page itself
  hides eBay listings once their lookup is six hours old. Every eBay card says how long ago
  it was fetched.
- eBay content in a "Public Display" may not be mixed with other listings. Caxi-Vaxi is
  not public: it is a private page for me and my partner, behind an invitation-only login,
  so eBay sits in the grid with everything else. The sharing page in `compartir.py`, which
  goes out with an open link, still leaves it out.
- No eBay user IDs may be stored. The reader keeps the piece and drops the seller entirely,
  which is also what the "Not persisting eBay data" exemption from eBay's account-deletion
  notifications declares.
- eBay data may not be used to model prices, so it never feeds `comparables.py`.

The footer carries a trademark notice next to Etsy's.

## Wallapop

Wallapop's `robots.txt` forbids `/search`, `/app/` and anything with a `?`, and allows the
rest. Three kinds of page are read, and all three carry their data in the `__NEXT_DATA__`
block, so no JavaScript runs:

- **Listings I saved** (`WALLAPOP_ARTICULOS` in `config_local.py`): price, description,
  condition, location, and whether it is reserved or sold.
- **Sellers I follow** (`WALLAPOP_VENDEDORES`): a profile shows the seller's first 40
  listings. The rest would need a `?` or the API, so for a big seller that is all there is.
- **Themed landing pages** (`WALLAPOP_PORTADAS`, with fifteen Madrid pages by default:
  sideboards, chests of drawers, armchairs, desk lamps, mirrors, sculpture and so on):
  Wallapop publishes these for search engines, 80 listings each. It only makes them for
  popular searches, so "silla thonet" or "busto" have none. Each page links to related
  ones; `wallapop.py --descubrir` tries the ones that sound like my taste and adds the
  ones that exist to the daily pass.

Slugs or full URLs pasted from the browser both work. One pass a day, eighty pages at most,
three seconds apart, and a full stop on any 403, keeping the previous pass. Each pass
overwrites `datos/wallapop.json` and compares it with the last one: price drops (which count
as an opportunity, like a shop's markdown), newly reserved or sold pieces, saved listings
that disappeared, and new listings from a followed seller. Changes are printed at the end.

Wallapop sellers write sizes number first ("190cm ancho x 42cm fondo") and paste tag lists
for search ("space age, minimalista, retro, Danish..." or "tags: ..."). Both are handled.

Wallapop's terms of use (3.1.2, points 15 and 17) forbid bots even where `robots.txt`
allows them. This is one person's moderate personal use and I accept that risk. To find new
pieces beyond these pages, the prefilled search link on the page and the app's own "Guardar
búsqueda" alerts do the rest.

## Pamono, The Oblist and 1stDibs

All three were checked before writing any code (6 October 2026), and all three are read
without an account, one request every three seconds, with a full stop on any 403.

**The Oblist** moved to oblist.com and is a Shopify store whose `robots.txt` allows
everything except carts, accounts and search. Most of its catalogue is new and expensive, so
only three vintage collections are read, and only pieces under 900 €.

**Pamono** allows its category pages in `robots.txt` and says nothing about automated
access in its terms. Categories are read sorted by price, ascending, and the reader stops
on the first page that goes past the ceiling, so it rarely needs more than two pages. The
"contemporáneo" categories are left out on purpose. For storage, desks and nightstands it
also opens the product page once to get width, depth and height, and caches the result.
When Pamono marks a piece down, the old price counts as a price drop.

**1stDibs** forbids its search, item pages and any `?q=` in `robots.txt`, but allows category
pages and the `?price=` filter. Every category page carries a JSON-LD block with name, price,
photo, category and year, so product pages are never opened. Its user agreement asks users
to follow "accepted Internet protocol", which is what `robots.txt` is. Prices are in dollars
and the euro figure is approximate.

A shop does not announce a sale; the piece just disappears. Any fixed-price piece not seen
in the last four days is treated as sold and dropped from the page. Sold-out Shopify
products are skipped; they used to be marked "unsold", which was backwards.

## The page

`vista.py` writes one self-contained HTML file that works as a single search engine over every
source: type "silla", set the limits, and see the chairs from the auction houses, the shops,
Pamono, 1stDibs, Etsy, eBay and Wallapop at once, instead of going site by site. About 15,800
pieces, drawn 60 at a time as you scroll.

Europe only: anything known to be elsewhere (Odalys in Caracas, Etsy shops in the US) is left
out, and the country chips narrow it further. A piece whose source does not say where it is
(1stDibs, The Oblist, most of Pamono) shows under Europe but not under a single country.
Reserved Wallapop listings are left out.

Each card says only facts about the piece: the portal, where it is, the title, year,
dimensions, materials, price and shipping cost. Anything the source does not give is simply not
mentioned. The only vote is a like; liked pieces can be shown on their own.

The search panel ("Filtros") borrows its structure from Pamono and 1stDibs: what kind of thing
(the page expands "storage" into cómoda, cajonera, aparador, credenza and the rest of the
catalogue vocabulary), a minimum and maximum price, width, height and depth separately, whether
it has to fit through a door, materials, period, colour, marked-down only, and words to exclude.
Results sort by relevance (the taste profile), newest, or price. Briefs can be saved by name.

When there is a query, the same search is offered as ready-made links to Catawiki, Wallapop,
Milanuncios, eBay, Etsy, Vinted, Pamono, 1stDibs and The Oblist. Catawiki sits behind Akamai and
returns 403 to any automated request, `robots.txt` included, so it stays manual; its own
"Guardar búsqueda" sends alerts. Its buyer fee is 9% plus a fixed 3 €, VAT included.

The look follows my Juddaun design system (Judd plus Braun: repeated objects on a quiet field,
1px rules, one accent, no emoji) in a palette I call Klein: white, cool greys and one electric
blue. The audit behind the current version is in `AUDITORIA-DISENO.md`.

## Sharing a search

`compartir.py` turns the storage search into a phone page that can be published as a
private claude.ai Artifact and shared with one person, who votes with a heart. A published
page cannot load images from other sites, so it downloads one small thumbnail per piece
(220 x 275) and packs them a hundred to a JPEG mosaic; every piece links to its shop for the
real photographs. Etsy is left out, because its API terms forbid showing data older than
24 hours. Votes go to the Artifact's shared store, one document per person; whoever cannot
write there keeps their votes on their phone and can copy the list to send it.

## Layout

| File | Job |
|---|---|
| `perfil.py` | My taste, as weights. The only file worth editing often |
| `casas.py` | Each house, its premium, its storage charges, total cost |
| `scraper.py` | Reads the five houses. Rate limiting and stop conditions live here |
| `duran.py` | Durán loads lots over AJAX and needs its own adapter |
| `shopify.py` | Shops with an open `products.json`, including The Oblist |
| `tiendas.py` | Pamono and 1stDibs |
| `etsy.py` | Etsy, through its API |
| `ebay.py` | eBay.es, through its API; kept apart on the page |
| `wallapop.py` | Wallapop listings, sellers and landing pages, and what changed since last time |
| `tests/` | The eBay and Wallapop readers against made-up pages, no network |
| `compartir.py` | A search as a phone page to share and vote on |
| `marca/` | The whale, in two sizes |
| `puntuar.py` | Scoring, and the catalogue-vocabulary flags |
| `encargo.py` | Briefs with hard dimensional limits |
| `comparables.py` | Past hammer prices, matched within category and period |
| `vista.py` | Builds the page: scores, attributes, image sizes |
| `plantilla.py` | The page itself: search panel, grid, detail view |
| `marketplaces.py` | Search links for sites that cannot be read automatically |

## Where it is weak

`comparables.py` now only compares within the same category and a compatible period, uses
hammer prices where the archive has them, and refuses to give a verdict on fewer than six
comparables. That fixed the nonsense (it used to compare a 1960s sideboard against a
Carlos III writing desk), but it exposed the real limit: Alcalá's archive has 465 furniture
lots and nearly all are antiques. It gives a verdict on about a quarter of the lots that
match my taste, mostly sculpture, painting and ceramics. For mid-century furniture there is
no base to compare against yet.

The storage I am actually looking for is rare in these seven sources: nine lots out of
4,334 at last count. For that kind of piece the private-sale sites are where the stock is.
eBay and part of Wallapop can now be read, but Wallapop only through the pages listed
above, never its search.

The taste profile is my reading of my own taste, which is not the same as my taste. It gets
better when I feed it things I actually chose.

## One finding worth writing down

From Alcalá's own archive, 9,590 pairs of starting price and hammer price:

- **52%** of lots do not sell at all.
- Of those that do, **60%** go at the starting price or below.
- Median ratio of hammer to opening bid: **1.00x**. Only 9% double it.

So roughly three lots in ten are knocked down at the opening bid with nobody bidding against
you. Bidding wars are the exception. Leaving a modest bid on thirty lots beats fighting over
one.
