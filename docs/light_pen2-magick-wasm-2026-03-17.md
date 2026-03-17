# light_pen2 magick-wasm メモ

`light_pen2` は `magick-wasm` を使って、ブラウザ内で `RGBA16 + iCCP` の PNG を作る実験用フロントエンド。

## 目的

- `ImageMagick WASM` で 16-bit PNG を直接書けるか確認する
- `iCCP` 埋め込みを自前 PNG writer なしで完結できるか確認する
- `light_pen` と別ラインで、magick 系の表現を試せるようにする

## 現在の処理

1. 元画像を `magick-wasm` で読み込む
2. 出力サイズを長辺 `800px` 以内にリサイズする
3. 参照 ICC (`public/bt2020-pq.icc`) を出力側プロファイルとして設定する
4. 元画像を複製し、発光用レイヤーだけ `ColorSpace.RGB` で `EvaluateOperator.Multiply` を適用する
5. 描画キャンバスをグレースケール PNG にして `CopyAlpha` で発光レイヤーの alpha に転用する
6. 発光レイヤーをベースへ `Over` 合成する
7. `PNG` + `depth=16` で書き出す
8. 比較用に `iCCP` を外した `fail_no_iccp` も同時に書く

## 確認できたこと

- `magick-wasm` でローカル UI から PNG 出力まで動作した
- `HDR候補を生成` 実行後に `success_like` / `fail_no_iccp` の保存リンクが生成された
- `npm --prefix light_pen2 run build` は通る

## 制約

- SDR 入力を HDR ICC へどう変換するかは未確定で、背景色の見え方はまだ不安定
- `ColorSpace.RGB` の扱いは「線形倍率を試す」ための実験で、表示系との整合は要追加検証
- `cICP` の明示制御までは入れていない

## 次に見る点

- `success_like` の PNG chunk を調べ、`magick-wasm` 出力との差分を比較する
- `iCCP` だけでなく `cICP` も必要かを再確認する
- ICC 付き入力 PNG を優先的に使い、変換前後の色ズレを切り分ける
