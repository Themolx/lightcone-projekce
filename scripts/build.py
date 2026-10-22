"""Z data/raw.json vytvoří films.json, který načítá index.html."""
import datetime
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
films = json.load(open(os.path.join(ROOT, "data", "raw.json")))


def parse_meta(meta):
    parts = [p.strip() for p in meta.split(" / ")]
    r = {"ys": "", "y": None, "fmt": "", "col": "", "snd": "", "scr": "", "s": None}
    for p in parts:
        lp = p.lower()
        if re.fullmatch(r"\d{4}(\s*-\s*\d{4})?", p) and not r["ys"]:
            r["ys"] = p.replace(" ", "")
            r["y"] = int(p[:4])
        elif m := re.fullmatch(r"(\d+)\s*screens?", lp):
            n = int(m.group(1))
            r["scr"] = str(n) if n < 4 else "4+"
        elif m := re.fullmatch(r"(?:(\d+)h\s*)?(\d+)'\s*(\d+)?", p):
            r["s"] = int(m.group(1) or 0) * 3600 + int(m.group(2)) * 60 + int(m.group(3) or 0)
        elif lp in ("sound", "silent") or "sound" in lp:
            r["snd"] = "silent" if lp == "silent" else "sound"
        elif "b&w" in lp or "color" in lp or "colour" in lp:
            r["col"] = lp
        elif not r["fmt"] and r["ys"]:
            r["fmt"] = p
    return r


GAUGES = {"16mm", "35mm", "super 8", "8mm", "9,5mm", "9.5mm", "70mm", "super 16"}


def gauges(fmt):
    """Filmové formáty zvlášť, vše ostatní (HD, 2K, mobil…) jako digitál."""
    g = []
    for p in re.split(r"\s*&\s*", fmt):
        p = p.strip()
        if not p:
            continue
        lab = p if p.lower() in GAUGES else "video / digitál"
        if lab.lower() == "super 8":
            lab = "Super 8"
        if lab not in g:
            g.append(lab)
    return g


out = []
for f in films:
    if not f.get("videos"):
        continue
    m = parse_meta(f.get("meta") or "")
    authors = [a["name"] for a in f.get("filmmakers") or []] or [a.strip() for a in f["by"].split(",") if a.strip()]
    prints = f.get("prints") or []
    imgs = f.get("images") or []
    out.append({
        "id": f["id"],
        "t": f["title"],
        "a": authors,
        "u": f["url"],
        "v": f["videos"][0],
        "img": imgs[0] if imgs else f["thumb"],
        "imgs": imgs,
        "d": f.get("desc", "").replace("\r", ""),
        "dist": ", ".join(dict.fromkeys(p.get("distribution format", "") for p in prints if p.get("distribution format"))),
        "fee": " / ".join(dict.fromkeys(p.get("rental fee", "") for p in prints if p.get("rental fee"))),
        **m,
        "fg": gauges(m["fmt"]),
    })

out.sort(key=lambda f: -f["id"])
payload = {"updated": datetime.date.today().isoformat(), "films": out}
dest = os.path.join(ROOT, "films.json")
with open(dest, "w") as fh:
    json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))
print(len(out), "filmů ->", dest, round(os.path.getsize(dest) / 1e6, 2), "MB")
if "-v" in sys.argv:
    from collections import Counter
    print("fg", Counter(g for x in out for g in x["fg"]).most_common())
    for k in ("col", "snd", "scr"):
        print(k, Counter(x[k] for x in out).most_common(15))
    print("bez roku", sum(1 for x in out if not x["y"]), "bez délky", sum(1 for x in out if x["s"] is None))
