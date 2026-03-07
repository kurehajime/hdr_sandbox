# success_sample.png 再現候補の生成手順（第1版）

更新日: 2026-03-07

## 目的

`sample/success_sample.png` で確認できたプロファイル（16bit RGBA + iCCP(cicp=9/16/0/1)）を再現し、
成功候補と失敗候補を機械的に作り分ける。

## 追加スクリプト

- `scripts/make_candidates.py`

このスクリプトは以下を実行する:

1. 参照成功PNGから iCCP(ICC) を抽出
2. 入力画像を 400x400 RGBA に正規化
3. 下記4パターンを生成
   - `candidate_success_like.png`（成功候補）
   - `candidate_fail_8bit.png`
   - `candidate_fail_no_iccp.png`
   - `candidate_fail_rgb_no_alpha.png`
4. 比較レポート `generated/comparison.md` を出力

## 実行コマンド

```bash
python3 scripts/make_candidates.py \
  --input sample/success_sample.png \
  --success-ref sample/success_sample.png \
  --outdir generated
```

## 生成結果（機械判定）

`generated/comparison.md` より:

- `candidate_success_like.png`
  - 400x400 / 16bit / RGBA(ColorType 6)
  - iCCPあり
  - cicp=[9,16,0,1]
  - `match_target_profile = YES`
- `candidate_fail_8bit.png`
  - bit depth 8 のため `NO`
- `candidate_fail_no_iccp.png`
  - iCCPなしのため `NO`
- `candidate_fail_rgb_no_alpha.png`
  - color type 2 (RGB) のため `NO`

## 現時点の結論（暫定）

- 再現候補を生成するローカル手順は確立できた。
- `match_target_profile` 基準では、
  - 16bit
  - RGBA (ColorType 6)
  - iCCP内 cicp=[9,16,0,1]
  が揃うことが重要。

## 未完タスク

- 実機（Xアプリ/iPhone）での投稿結果比較（光り方）
- 投稿後配信物のメタ（再エンコード後の保持情報）確認

