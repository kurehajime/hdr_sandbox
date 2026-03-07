# success_sample.png 再現候補の生成手順（第2版）

更新日: 2026-03-07

## 目的

`sample/success_sample.png` を基準に、
HDRっぽく「光る/光らない」を切り分ける候補PNGを機械生成する。

## スクリプト

- `scripts/make_candidates.py`

このスクリプトは以下を実行する:

1. 参照成功PNGから iCCP(ICC) を抽出
2. 入力画像を 400x400 RGBA に正規化
3. 基本4パターンを生成
   - `candidate_success_like.png`（成功候補）
   - `candidate_fail_8bit.png`
   - `candidate_fail_no_iccp.png`
   - `candidate_fail_rgb_no_alpha.png`
4. （`--extended`指定時）追加切り分け候補を生成
   - `candidate_probe_8bit_rgb_no_alpha.png`
   - `candidate_probe_alpha_255.png`
   - `candidate_probe_alpha_0.png`
   - `candidate_probe_size_512.png`
5. 比較レポート `generated/comparison.md` を出力

## 実行コマンド

### 基本セット

```bash
python3 scripts/make_candidates.py \
  --input sample/success_sample.png \
  --success-ref sample/success_sample.png \
  --outdir generated
```

### 追加切り分けセット（推奨）

```bash
python3 scripts/make_candidates.py \
  --input sample/success_sample.png \
  --success-ref sample/success_sample.png \
  --outdir generated \
  --extended
```

## 生成結果（機械判定）

`generated/comparison.md` では以下2つの観点で表示する:

- `legacy`: 16bit + RGBA + iCCP/cicp を満たすか（旧仮説）
- `relaxed`: iCCP/cicp を満たすか（更新仮説）

## 人間検証結果（X投稿）

- `candidate_success_like`
  - https://x.com/kurehajime/status/2030233227521302817
  - → 光って見えた
- `candidate_fail_rgb_no_alpha`
  - https://x.com/kurehajime/status/2030233123523547149
  - → 光って見えた
- `candidate_fail_no_iccp`
  - https://x.com/kurehajime/status/2030232947044110346
  - → 光って見えない
- `candidate_fail_8bit`
  - https://x.com/kurehajime/status/2030232680877723982
  - → 光って見えた

## 結論（2026-03-07時点）

- 「16bit必須」「alpha必須」は人間検証で反証された。
- 現時点では **iCCP内 cicp=[9,16,0,1] 主導**の仮説が有力。
- 詳細な仮説更新と次実験計画は
  `docs/hypothesis-update-2026-03-07.md` を参照。
