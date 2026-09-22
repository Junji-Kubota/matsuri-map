"""Wikimedia Commons から、自由に使える祭りの写真を探して保存する。

使い方:
  python tools/commons_photos.py search 2 "Nebuta Matsuri"          候補を一覧表示
  python tools/commons_photos.py search 2 "青森ねぶた" --preview      候補の縮小画像も photos/_candidates/2/ に保存
  python tools/commons_photos.py add 2 "File:Aomori Nebuta 2019.jpg"  写真を保存し、クレジットを記録

使ってよいライセンス: CC0 / パブリックドメイン / CC BY / CC BY-SA
（NC（非営利限定）や ND（改変禁止）、ライセンス不明のものは除外する）
標準ライブラリだけで動きます。
"""
import json
import re
import sys
import urllib.parse
import urllib.request
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DETAILS = ROOT / "festival_details.json"
PHOTOS = ROOT / "photos"
API = "https://commons.wikimedia.org/w/api.php"
UA = "matsuri-map-personal/1.0 (personal festival map; uses Wikimedia Commons API)"
MAX_PER_FESTIVAL = 3
WIDTH = 1280

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def api(params):
    params = {**params, "format": "json", "formatversion": "2"}
    return json.loads(get(API + "?" + urllib.parse.urlencode(params)))


def plain(html):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", html or ""))).strip()


def license_ok(short):
    s = (short or "").upper()
    if not s or "NC" in s or "ND" in s or "FAIR USE" in s:
        return False
    return ("CC0" in s or "PUBLIC DOMAIN" in s or s.startswith("PD")
            or re.match(r"CC BY(-SA)? ?\d", s) is not None or s in ("CC BY", "CC BY-SA"))


def info_from_page(p):
    ii = (p.get("imageinfo") or [{}])[0]
    meta = ii.get("extmetadata", {})
    val = lambda k: (meta.get(k) or {}).get("value", "")
    return {
        "title": p.get("title", ""),
        "license": plain(val("LicenseShortName")),
        "license_url": plain(val("LicenseUrl")),
        "author": plain(val("Artist")) or plain(val("Credit")) or "不明",
        "description": plain(val("ImageDescription"))[:160],
        "mime": ii.get("mime", ""),
        "size": f"{ii.get('width', '?')}x{ii.get('height', '?')}",
        "thumb": ii.get("thumburl", ""),
        "source": ii.get("descriptionurl", ""),
    }


def search(fid, query, limit=15, preview=False):
    data = api({"action": "query", "generator": "search", "gsrsearch": query, "gsrnamespace": 6,
                "gsrlimit": limit, "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime",
                "iiurlwidth": WIDTH})
    pages = sorted(data.get("query", {}).get("pages", []), key=lambda p: p.get("index", 0))
    out = []
    for p in pages:
        c = info_from_page(p)
        if c["mime"] not in ("image/jpeg", "image/png") or not license_ok(c["license"]):
            continue
        out.append(c)
    if preview and out:
        d = PHOTOS / "_candidates" / str(fid)
        d.mkdir(parents=True, exist_ok=True)
        for i, c in enumerate(out, 1):
            try:
                (d / f"{i:02d}.jpg").write_bytes(get(c["thumb"]))
                c["preview"] = str((d / f"{i:02d}.jpg").relative_to(ROOT))
            except Exception as e:
                c["preview"] = f"取得失敗: {e}"
    print(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"\n使える候補: {len(out)}件（ライセンスで除外したものは表示していません）")


def add(fid, titles):
    details = json.loads(DETAILS.read_text(encoding="utf-8"))
    if fid not in details:
        sys.exit(f"festival_details.json に id {fid} がありません")
    entry = details[fid]
    photos = entry.setdefault("photos", [])
    data = api({"action": "query", "titles": "|".join(titles), "prop": "imageinfo",
                "iiprop": "url|extmetadata|size|mime", "iiurlwidth": WIDTH})
    folder = PHOTOS / fid
    folder.mkdir(parents=True, exist_ok=True)
    for p in data.get("query", {}).get("pages", []):
        c = info_from_page(p)
        if p.get("missing"):
            print(f"見つかりません: {c['title']}"); continue
        if not license_ok(c["license"]):
            print(f"ライセンスが対象外のため追加しません: {c['title']}（{c['license'] or '不明'}）"); continue
        if any(x.get("source") == c["source"] for x in photos):
            print(f"追加済み: {c['title']}"); continue
        if len(photos) >= MAX_PER_FESTIVAL:
            print(f"1件あたり{MAX_PER_FESTIVAL}枚までです。これ以上は追加しません"); break
        ext = ".png" if c["mime"] == "image/png" else ".jpg"
        n = 1
        while (folder / f"{n}{ext}").exists():
            n += 1
        path = folder / f"{n}{ext}"
        path.write_bytes(get(c["thumb"]))
        photos.append({"file": path.relative_to(ROOT).as_posix(), "author": c["author"], "license": c["license"],
                       "license_url": c["license_url"], "source": c["source"], "title": c["title"]})
        print(f"保存しました: {path.relative_to(ROOT).as_posix()}（{c['author']} / {c['license']}）")
    DETAILS.write_text(json.dumps(details, ensure_ascii=False, indent=1), encoding="utf-8")


def main():
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == "search":
        search(a[1], a[2], preview="--preview" in a)
    elif len(a) >= 3 and a[0] == "add":
        add(a[1], a[2:])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
