-- Caxi-Vaxi.app (~/Applications): abre la pagina al instante y, en segundo
-- plano, actualiza solo si toca (actualizar.py si-toca: completa si la ultima
-- tiene mas de 24 h, solo eBay si sus datos pasan de 6 h, si no nada).
-- Avisa con una notificacion de macOS al empezar y al acabar.
-- Para reinstalarlo:
--   osacompile -o ~/Applications/Caxi-Vaxi.app/Contents/Resources/Scripts/main.scpt marca/app-caxi-vaxi.applescript
--   codesign --force --deep -s - ~/Applications/Caxi-Vaxi.app
do shell script "open '/Users/diego/Projects/Claude Code/caxi-vaxi/datos/vista.html'"
do shell script "cd '/Users/diego/Projects/Claude Code/caxi-vaxi' && nohup .venv/bin/python -W ignore actualizar.py si-toca --avisar > /dev/null 2>&1 &"
