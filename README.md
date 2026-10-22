# Light Cone Projekce

Neoficiální vyhledávač ve filmech z katalogu [Light Cone](https://lightcone.org/en), které mají online ukázku.
Ukázky si můžeš rovnou přehrát.

**Web:** https://themolx.github.io/lightcone-projekce/

- vyhledávání podle názvu, filmaře i popisu za psaní (bez diakritiky, `-slovo` vyloučí, `"fráze"` hledá přesně)
- filtry: rok a dekáda, délka, barva, zvuk, materiál (16mm, Super 8, 35mm, digitál…), počet pláten
- náhled bez zvuku při najetí myší, přehrávač s popisem, šipky ← → pro další film, `R` pro náhodný
- uložené filmy a filtr „ještě neviděné“ (ukládá se jen v tvém prohlížeči)
- odkazy: `?q=hledaný+výraz`, `?author=Stan+BRAKHAGE`, `?film=16652`

Videa a obrázky se načítají přímo ze serverů Light Cone. Repo obsahuje jen index metadat a odkazy.
Všechna práva k filmům, textům a obrázkům má Light Cone a autoři filmů.

## Aktualizace dat

GitHub Action [`update.yml`](.github/workflows/update.yml) běží každé pondělí. Projde seznam filmů s ukázkou,
stáhne detail jen u nových filmů a uloží `films.json`. Spustit ji jde i ručně (Actions → Aktualizace katalogu → Run workflow).

Ručně:

```bash
python3 scripts/scrape.py   # data/raw.json
python3 scripts/build.py    # films.json
python3 -m http.server      # pak http://localhost:8000
```

## Rozšíření pro Chrome

Složka [`extension/`](extension) přidává do webu lightcone.org:

- tlačítko **▶ Přehrát ukázku** a náhled při najetí myší u každého filmu s ukázkou ve výsledcích hledání, na stránkách filmařů a v novinkách
- odkaz do Projekce na stránkách filmů, filmařů a výsledků hledání
- klik na ikonu rozšíření otevře Projekci

Instalace: `chrome://extensions` → zapnout **Režim pro vývojáře** → **Načíst rozbalené** → vybrat složku `extension`.
