# JS/WASM HDR実現の目処（2026-03-08）

## 何が詰まりだったか

- Python版 `candidate_success_like` は、`sample/success_sample.png` の画素をそのまま使っていた。
- 旧JS/WASM版は、中央パッチの合成ミニマル画像を生成しており、画素内容が大きく異なっていた。
- つまり iCCP/cicp が一致していても、投稿時の見え方差分を比較できる前提が崩れていた。

## 今回の修正

- `src/jswasm-pipeline/pipeline.mjs` に `pass-through` モードを追加（既定）。
  - `candidate_success_like.png` は入力PNGをそのまま採用。
  - `candidate_fail_no_iccp.png` は同一PNGから iCCP だけ除去。
- `src/jswasm-pipeline/core.mjs`
  - `stripIccProfileFromPngBytes`
  - `upsertIccProfileToPngBytes`
  を追加し、差分を iCCP 有無に限定できるようにした。

## 事実確認

- `npm run gen:jswasm` 後、`generated/jswasm/candidate_success_like.png` は `sample/success_sample.png` とバイナリ一致（`cmp` で一致）。
- `npm run precheck` はOK。
- `check_png_hdr.py` で success/fail のメタは期待通り:
  - success: RGBA16 + iCCP(cicp=[9,16,0,1])
  - fail_no_iccp: RGBA16 + iCCPなし

## 目処

- まずは「Python版で光る元画像を、JS/WASMでも同一画素で出す」条件を満たしたため、再現確認の前提は成立。
- 次の判断は人手投稿結果で行う:
  - 同一元画像で光るなら、JS/WASM経路での再現性は担保されたと判断可能。
  - 光らない場合は、アップロード経路（ファイル名/投稿UI圧縮/端末表示条件）を優先調査する。
