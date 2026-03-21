# light_pen2: ICC 後付け構成メモ

`light_pen2` では、`magick-wasm` に HDR ICC 適用まで任せると入力画素が大きく変わることが分かりました。

## 変更後の構成

- `magick-wasm`
  - リサイズ
  - マスク生成と `CopyAlpha`
  - `EvaluateOperator.Multiply` による露光ブースト
  - `MagickFormat.Png64` での 16-bit PNG 書き出し
- `src/hdr/core.mjs`
  - `success_sample.png` から抽出した ICC を `iCCP` として後付け
  - `fail_no_iccp` 側では `iCCP` を除去

## 理由

- `sample/giant.png` で確認すると、`setProfile(targetProfile)` だけで平均絶対差が `122.59 / 118.13 / 138.92 / 0` 発生した
- `transformColorSpace(sourceProfile, targetProfile)` を追加しても差分はほぼ同じで、主因は HDR ICC 適用そのものだった
- 一方で `Png64` 書き出しや `depth=16` 化だけでは差分 `0 / 0 / 0 / 0` だった

## 検証結果

- 条件
  - 入力: `sample/giant.png`
  - 線なし
  - `露光ゲイン=1.0`
- 変更後
  - 元画像 vs `candidate_fail_no_iccp.png` の生ピクセル差分: `0 / 0 / 0 / 0`
  - `candidate_success_like.png` vs `candidate_fail_no_iccp.png` の生ピクセル差分: `0 / 0 / 0 / 0`
  - 両方とも `IHDR bitDepth=16 colorType=6`
  - `success_like` のみ `iCCP` あり

## 含意

- 今の `light_pen2` は「画素は維持し、ICC だけを差し替える」方針になった
- ブラウザプレビューでは `success_like` の見た目が大きく変わることがあるが、これは ICC 解釈の影響を含む
- X で HDR として成立するかは引き続き実投稿で確認が必要
