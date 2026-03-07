# success_sample.png 再現候補の生成手順（第3版）

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
   - `candidate_probe_alpha_1.png`（白化回避プローブ）
   - `candidate_probe_alpha_gradient.png`（白化回避プローブ）
   - `candidate_probe_size_512.png`
   - `candidate_probe_size_512_nontransparent.png`（白化回避プローブ）
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

### 基本4候補

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

### extended候補（既実施分）

- `candidate_probe_8bit_rgb_no_alpha.png`
  - https://x.com/kurehajime/status/2030240958701568112
  - → 光って見えた
- `candidate_probe_alpha_255.png`
  - https://x.com/kurehajime/status/2030241207994159531
  - → 光って見えた
- `candidate_probe_alpha_0.png`
  - → 真っ白でなにも見えず
- `candidate_probe_size_512.png`
  - → 真っ白でなにも見えず

## 白化観測の解釈（2026-03-07追記）

- `alpha=0` は「完全透明」なので、HDR判定以前に表示合成で内容が消える（白化に見える）可能性が高い。
- `size=512` の白化は、サイズ単独要因とは断定せず、透明度分布との相互作用も疑う。
- したがって、白化観測は `iCCP/cicp` 仮説の直接反証とは扱わず、
  **白化回避プローブ（alpha=1 / alphaグラデーション / 512+非透明）で再検証**する。

## 結論（2026-03-07時点）

- 「16bit必須」「alpha必須」は人間検証で反証された。
- 現時点では **iCCP内 cicp=[9,16,0,1] 主導**の仮説が有力。
- 白化観測を踏まえ、透明度条件を制御した追加プローブで次段の切り分けを行う。
- 詳細な仮説更新は `docs/hypothesis-update-2026-03-07.md` を参照。
