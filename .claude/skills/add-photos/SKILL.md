---
name: add-photos
description: 祭りの代表的な写真を Wikimedia Commons から自由に使えるライセンスで2〜3枚探し、photos フォルダに保存してクレジットを記録し、地図を作り直す。「写真を追加して」「〇〇祭りに写真を入れて」と言われたときに使う。
---

# 祭りの写真を追加する

引数：祭りの id か名前（複数可）。「全部」「写真のない祭り」なら、festival_details.json で photos が空のものすべて。

## 守ること

- 写真は **Wikimedia Commons から、CC0・パブリックドメイン・CC BY・CC BY-SA のものだけ** を使う。公式サイトや観光サイト、SNSの写真は使わない。
- 1件あたり最大3枚。撮影者・ライセンス・元のページは `tools/commons_photos.py` が自動で記録するので、手で消さない。
- 特定の個人（とくに子ども）の顔が大きく写った写真は選ばない。祭りの全体や山車・踊りの様子がわかる写真を選ぶ。
- その祭りの写真だと確認できないもの（別の祭り、別の年の別行事、説明が曖昧なもの）は使わない。

## 手順（祭りごと）

1. **探す**
   `python tools/commons_photos.py search <id> "<検索語>" --preview`
   検索語は英語名（例 `Nebuta Matsuri Aomori`）と日本語名（例 `青森ねぶた祭`）の両方で試す。
   候補の縮小画像が `photos/_candidates/<id>/` に保存されるので、画像を実際に見て確認する。

2. **選ぶ**
   2〜3枚を選ぶ。できれば「全体の様子」「主役（山車・神輿・踊り手など）の近景」「夜や別の場面」のように、違う見え方の写真を組み合わせる。

3. **保存する**
   `python tools/commons_photos.py add <id> "File:〇〇.jpg" "File:△△.jpg"`
   写真は `photos/<id>/1.jpg` などに保存され、festival_details.json の `photos` にクレジットが追記される。

4. **後片付け**
   すべて終わったら `photos/_candidates/` フォルダを削除する。

5. **地図を作り直す**
   `python build_map.py` を実行する。

6. **報告する**
   祭りごとに追加した枚数を伝える。使える写真が見つからなかった祭りは、その旨と試した検索語を伝える。
