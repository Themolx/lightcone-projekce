"""Light Cone: stáhne katalog filmů s video ukázkou do data/raw.json.

Spuštění: python3 scripts/scrape.py
Seznam filmů se stahuje vždy znovu, detail jen u filmů, které v data/raw.json ještě nejsou.
"""
import html
import http.cookiejar
import json
import os
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw.json")
BASE = "https://lightcone.org/en"
UA = "Mozilla/5.0 (lightcone-projekce catalogue index; +https://github.com/Themolx/lightcone-projekce)"
WORKERS = 3
DELAY = 0.4

jar = http.cookiejar.CookieJar()
# Python z python.org na macOS nemá certifikáty systému
ctx = ssl.create_default_context(cafile="/etc/ssl/cert.pem" if os.path.exists("/etc/ssl/cert.pem") else None)
opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(jar), urllib.request.HTTPSHandler(context=ctx)
)
opener.addheaders = [("User-Agent", UA)]


def get(url, data=None, tries=4):
    for i in range(tries):
        try:
            body = urllib.parse.urlencode(data).encode() if data else None
            with opener.open(url, body, timeout=40) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            print("  retry", url, e, flush=True)
            time.sleep(3 * (i + 1))
    return ""


def text(s):
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"</p>\s*<p>", "\n\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s).replace("\xa0", " ").replace("\r", "")
    return re.sub(r"[ \t]+", " ", s).strip()


ITEM = re.compile(
    r'miniatures116x79/(\d+)\.jpg.*?<a href="https://lightcone\.org/en/(film-(\d+)-[^"]+)">(.*?)</a>'
    r".*?<i>(.*?)</i>.*?<br>(.*?)</td>",
    re.S,
)


def list_pages():
    first = get(BASE + "/catalogue", {
        "recherche_catalogue_type": "avancee",
        "recherche_catalogue_critere_video": "true",
        "recherche_catalogue_critere_annee_min": "-1",
        "recherche_catalogue_critere_annee_max": "-1",
    })
    total = int(re.search(r"(\d+) MOVIES FOUND", first).group(1))
    last = max(int(p) for p in re.findall(r'\?page=(\d+)', first))
    print("celkem", total, "filmů,", last, "stránek", flush=True)
    films = {}
    for page in range(1, last + 1):
        src = first if page == 1 else get(f"{BASE}/catalogue?page={page}")
        for thumb, slug, fid, title, meta, by in ITEM.findall(src):
            by = text(by)
            films[fid] = {
                "id": int(fid),
                "url": f"{BASE}/{slug}",
                "title": text(title),
                "list_meta": text(meta),
                "by": by[3:] if by.startswith("by ") else by,
                "thumb": f"https://lightcone.org/media/miniatures116x79/{thumb}.jpg",
            }
        if page % 20 == 0:
            print("  stránka", page, len(films), flush=True)
        time.sleep(DELAY)
    # stránkování se při souběžných změnách katalogu může posunout; chybějící je nevadí, doplní příští běh
    if len(films) < total * 0.9:
        sys.exit(f"Seznam je podezřele krátký ({len(films)} z {total}), končím bez uložení.")
    return films


def film_detail(f):
    src = get(f["url"])
    main = src.split('id="main"', 1)[-1].split('id="footer"', 1)[0]
    d = {}
    d["videos"] = re.findall(r'<video[^>]*src="([^"]+)"', main)
    m = re.search(r"<i>(.*?)</i>", main, re.S)
    d["meta"] = text(m.group(1)) if m else ""
    d["filmmakers"] = [
        {"name": text(n), "url": u}
        for u, n in re.findall(r'<a href="(https://lightcone\.org/en/filmmaker-[^"]+)">(.*?)</a>', main)
    ]
    desc = re.search(r"</video>\s*<br>\s*<br>\s*(.*?)<h2>", main, re.S) or re.search(
        r"</table>\s*<br>\s*(<p>.*?)<h2>", main, re.S
    )
    d["desc"] = text(desc.group(1)) if desc else ""
    imgs = re.findall(r"miniatures220x150/(\d+)\.jpg", src)
    d["images"] = [f"https://lightcone.org/media/miniatures220x150/{i}.jpg" for i in imgs]
    copies = []
    for tbl in re.findall(r'<table class="copie".*?</table>', main, re.S):
        row = {text(k): text(v) for k, v in re.findall(r"<th>(.*?)</th>\s*<td>(.*?)</td>", tbl, re.S)}
        copies.append(row)
    d["prints"] = copies
    time.sleep(DELAY)
    return d


def save(films):
    data = sorted(films.values(), key=lambda f: -f["id"])
    with open(RAW, "w") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=0)


def main():
    cache = {}
    if os.path.exists(RAW):
        cache = {str(f["id"]): f for f in json.load(open(RAW))}
    films = list_pages()
    for fid, f in films.items():
        old = cache.get(fid)
        if old and old.get("videos"):
            f.update({k: old[k] for k in ("videos", "meta", "filmmakers", "desc", "images", "prints")})
    todo = [f for f in films.values() if not f.get("videos")]
    print("nových / bez detailu:", len(todo), "odstraněno:", len(set(cache) - set(films)), flush=True)
    done = 0
    with ThreadPoolExecutor(WORKERS) as ex:
        for f, d in zip(todo, ex.map(film_detail, todo)):
            f.update(d)
            done += 1
            if done % 100 == 0:
                print("  detail", done, "/", len(todo), flush=True)
                save(films)
    save(films)
    print("hotovo", len(films), "filmů,", sum(1 for f in films.values() if f.get("videos")), "s videem", flush=True)


if __name__ == "__main__":
    main()
