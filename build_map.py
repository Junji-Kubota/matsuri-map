"""festivals.csv と festival_details.json から matsuri-map.html を作る。

使い方:  python build_map.py                 （PCで開く地図。写真は photos フォルダを参照）
        python build_map.py --for-publish   （公開版用。写真は photo_assets.json のURLを使う）
標準ライブラリだけで動きます。問題があればエラーの内容を表示して止まります。
"""
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "festivals.csv"
DETAILS_PATH = ROOT / "festival_details.json"
TEMPLATE_PATH = ROOT / "map" / "template.html"
OUT_PATH = ROOT / "matsuri-map.html"
PHOTO_ASSETS = ROOT / "photo_assets.json"

CSV_REQUIRED = ["id", "name", "prefecture", "city", "lat", "lon", "period",
                "official_url", "source_url", "checked_on", "notes", "month", "next_date",
                "genre", "days", "best_time", "nearest_station", "station_kubun", "travel_hours_tokyo"]
TYPES = {"dashi", "mikoshi", "odori", "akari", "yuki", "sake", "tsuna", "hanabi", "hi"}
LEVELS = {"furatto", "keikaku", "honki"}
AXES = ["move", "stay", "view", "body"]
JOIN = {"see", "drop", "prep"}
GENRES = {"祭り", "踊り", "花火", "酒・ビール", "行事"}
BEST_TIMES = {"未明", "早朝", "日中", "夜"}


def fail(msgs):
    print("地図を作れませんでした。次の点を直してください:")
    for m in msgs:
        print("  - " + m)
    sys.exit(1)


def main():
    for_publish = "--for-publish" in sys.argv
    assets = json.loads(PHOTO_ASSETS.read_text(encoding="utf-8")) if (for_publish and PHOTO_ASSETS.exists()) else {}
    errors = []
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing = [c for c in CSV_REQUIRED if c not in (reader.fieldnames or [])]
        if missing:
            fail([f"festivals.csv に列がありません: {', '.join(missing)}"])
        rows = list(reader)
    details = json.loads(DETAILS_PATH.read_text(encoding="utf-8"))

    ids = [r["id"].strip() for r in rows]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        errors.append(f"id が重複しています: {', '.join(sorted(dup))}")

    out = []
    for r in rows:
        rid = r["id"].strip()
        label = f"id {rid}（{r['name']}）"
        try:
            lat, lon = float(r["lat"]), float(r["lon"])
            if not (20 <= lat <= 46 and 122 <= lon <= 154):
                errors.append(f"{label}: 緯度経度が日本の範囲外です ({lat}, {lon})")
        except ValueError:
            errors.append(f"{label}: 緯度経度が数字ではありません")
        months = [m for m in r["month"].split(";") if m.strip()]
        if not months or not all(m.strip().isdigit() and 1 <= int(m) <= 12 for m in months):
            errors.append(f"{label}: month は 1〜12 をセミコロン区切りで（例 7;8）")
        if r["next_date"].strip():
            try:
                datetime.strptime(r["next_date"].strip(), "%Y-%m-%d")
            except ValueError:
                errors.append(f"{label}: next_date は YYYY-MM-DD 形式で")
        if r["genre"].strip() not in GENRES:
            errors.append(f"{label}: genre は {'/'.join(sorted(GENRES))} のどれか")
        try:
            stay_days = int(r["days"].strip())
            if stay_days < 1:
                raise ValueError
        except ValueError:
            errors.append(f"{label}: days は1以上の整数で")
            stay_days = None
        best_times = [t for t in r["best_time"].split(";") if t.strip()]
        if not best_times or not all(t.strip() in BEST_TIMES for t in best_times):
            errors.append(f"{label}: best_time は {'/'.join(BEST_TIMES)} をセミコロン区切りで")

        d = details.get(rid)
        if d is None:
            errors.append(f"{label}: festival_details.json に対応する項目がありません")
            continue
        e = d.get("ease", {})
        if d.get("type") not in TYPES:
            errors.append(f"{label}: type は {', '.join(sorted(TYPES))} のどれか")
        if e.get("level") not in LEVELS:
            errors.append(f"{label}: ease.level は furatto / keikaku / honki のどれか")
        for ax in AXES:
            v = e.get(ax)
            if not (isinstance(v, list) and v and v[0] in (1, 2, 3)):
                errors.append(f"{label}: ease.{ax} は [1〜3, \"ひと言（省略可）\"] の形で")
        if not (isinstance(e.get("join"), list) and len(e["join"]) == 2 and e["join"][0] in JOIN):
            errors.append(f"{label}: ease.join は [\"see|drop|prep\", \"説明\"] の形で")
        photos = []
        for ph in d.get("photos", []) or []:
            f = ph.get("file", "")
            if not f or not (ROOT / f).exists():
                errors.append(f"{label}: 写真ファイルがありません: {f}")
                continue
            if not ph.get("author") or not ph.get("license"):
                errors.append(f"{label}: 写真のクレジット（author / license）がありません: {f}")
            item = {k: ph.get(k, "") for k in ("file", "author", "license", "license_url", "source")}
            if for_publish:
                if f in assets:
                    item["url"] = assets[f]
                else:
                    errors.append(f"{label}: 公開版に未アップロードの写真: {f}")
            photos.append(item)
        aud = d.get("audience", {})
        if aud.get("scale") not in (1, 2, 3, 4, 5):
            errors.append(f"{label}: audience.scale は 1〜5")

        base = {k: r[k].strip() for k in CSV_REQUIRED if k != "days"}
        out.append({
            **base,
            # CSVの "days"（参加に必要な日数）は stay_days に。
            # "days" はテンプレート側で「次回開催までの残り日数」として計算し直すため、
            # 同じキー名で渡すと上書きされてしまう。
            "stay_days": stay_days,
            "type": d.get("type"), "lead": d.get("lead", ""), "tips": d.get("tips", []),
            "trivia": d.get("trivia", ""),
            "lv": e.get("level"), "prep": e.get("prep", ""), "enote": e.get("note", ""),
            "ax": {ax: e.get(ax) for ax in AXES}, "join": e.get("join"), "aud": aud, "photos": photos,
            "ic": e.get("ic", ""), "offset": d.get("offset"),
        })

    extra = sorted(set(details) - set(ids), key=lambda s: int(s) if s.isdigit() else 0)
    if extra:
        errors.append(f"festival_details.json にだけある id: {', '.join(extra)}（CSVに行を足すか、削除を）")
    if errors:
        fail(errors)

    html = TEMPLATE_PATH.read_text(encoding="utf-8")
    html = html.replace("__ROWS__", json.dumps(out, ensure_ascii=False))
    html = html.replace("__BUILT__", datetime.now().strftime("%Y-%m-%d %H:%M"))
    out_path = ROOT / "matsuri-map-publish.html" if for_publish else OUT_PATH
    out_path.write_text(html, encoding="utf-8")
    n_ph = sum(len(x["photos"]) for x in out)
    print(f"{out_path.name} を作りました（{len(out)}件・写真{n_ph}枚）")


if __name__ == "__main__":
    main()
