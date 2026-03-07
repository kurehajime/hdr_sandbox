# 成功例解析: IMG_0892.PNG

更新日: 2026-03-07

## 入力

- ユーザー提供: `IMG_0892.zip`
- 展開ファイル: `IMG_0892.PNG`

## 解析結果（機械確認）

- フォーマット: PNG
- 解像度: 400x400
- Bit depth: 16
- Color Type: 6 (Truecolor + Alpha / RGBA)
- iCCP: あり
- ICC内 `cicp` タグ: あり
  - `primaries=9` (BT.2020)
  - `transfer=16` (PQ / SMPTE ST 2084)
  - `matrix=0` (RGB)
  - `range=1` (Full)

## 意味

少なくともこの成功例では、以下の組み合わせでX(iPhoneアプリ)上で「光って見える」挙動が確認された。

- 16bit RGBA PNG
- iCCP内に BT.2020 + PQ 相当の `cicp` 情報

## 暫定の再現ターゲット

1. 400x400 PNG
2. 16bit RGBA
3. ICC `cicp = [9,16,0,1]`
4. Xアップロード時に編集を入れない

## 注意

- これは1サンプルの成功条件であり、必要条件・十分条件の切り分けは未完。
- 次ステップは、成功画像との差分比較（失敗画像との比較）と、投稿後配信実体のメタ残存確認。