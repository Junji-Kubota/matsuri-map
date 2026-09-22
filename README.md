# 行きたい祭り地図

将来行ってみたい日本各地の祭りを集めて、地図の上で眺めながら旅の計画を立てるためのサイトです。出発地はつつじヶ丘（東京都調布市）を基準にしています。

**サイトを見る：** <!-- GitHub Pages公開後にURLを追記 -->

## できること

- 地方・開催月・行きやすさで絞り込んで祭りを探せる
- 各祭りの見どころ・楽しみ方のコツ・豆知識
- 行きやすさの目安（移動・宿・観覧・体力の4軸、準備の目安）
- 人出（主催者・報道の発表値）
- 最寄りの高速道路インターチェンジ、新幹線駅、空港（簡略地図）
- Wikimedia Commonsの自由ライセンス写真（CC0 / CC BY / CC BY-SA）

## 仕組み

| ファイル | 役割 |
|---|---|
| `festivals.csv` | 祭りの基本情報（1行1祭り）。正本 |
| `festival_details.json` | 見どころ・コツ・豆知識・行きやすさ・人出・写真クレジット。正本 |
| `build_map.py` | 上記2つと `map/template.html` から `matsuri-map.html` を生成するスクリプト |
| `map/template.html` | 地図のデザインと地理データ |
| `photos/<id>/` | 祭りごとの写真（Wikimedia Commons由来、クレジットは `festival_details.json` に記録） |
| `tools/commons_photos.py` | Wikimedia Commonsから写真を検索・保存するツール |

`festivals.csv` や `festival_details.json` を更新して `main` ブランチにpushすると、GitHub Actionsが自動で `python build_map.py` を実行し、GitHub Pagesに反映します。

## ローカルで動かす

```bash
python build_map.py
```

標準ライブラリのみで動きます。生成された `matsuri-map.html` をブラウザで開けば確認できます。

## データについて

- 開催日程・座標・出典は確認できたものだけを記載し、確証が持てない項目は空欄にしています（`notes` 列に「要確認」と記載）。
- 次回開催日は、公式発表がない場合は例年のルールから計算した推定値です（`notes` に「次回日程は推定」と記載）。出かける前に必ず公式サイトでご確認ください。
- 写真はすべてWikimedia CommonsのCC0・パブリックドメイン・CC BY・CC BY-SAのものを使用し、撮影者・ライセンス・出典を記録しています。
