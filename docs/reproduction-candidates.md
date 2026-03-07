# success_sample.png 再現候補の生成手順（第4版）

更新日: 2026-03-07

## 目的

`sample/success_sample.png` を基準に、
HDRっぽく「光る/光らない」の境界を切り分ける候補PNGを機械生成する。

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
   - `candidate_probe_alpha_1.png`
   - `candidate_probe_alpha_16.png`（新規）
   - `candidate_probe_alpha_64.png`（新規）
   - `candidate_probe_alpha_gradient.png`
   - `candidate_probe_alpha_lr_split_16_64.png`（新規・左右分割）
   - `candidate_probe_size_512.png`
   - `candidate_probe_size_512_nontransparent.png`
   - `candidate_probe_size_512_alpha255_bright_patch.png`（新規）
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

### extended候補（既実施）

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

### extended候補（最新）

- `candidate_probe_alpha_gradient.png`
  - https://x.com/kurehajime/status/2030244873153175737
  - → 右半分のみ光る。左半分は黒っぽく見える
- `candidate_probe_alpha_1.png`
  - → 真っ白でなにも見えず
- `candidate_probe_size_512_nontransparent.png`
  - → 真っ黒でなにも見えず

## 新仮説（2026-03-07時点）

- 16bit必須 / alpha必須は反証済み
- iCCP内 `cicp=[9,16,0,1]` は有力条件
- ただし最終的な見え方は、
  **透明度(alpha) × 実効輝度 × 表示しきい値** の組み合わせで決まる可能性が高い

## 次に観測するポイント

新規追加プローブでは次を確認する:

- `alpha=16` と `alpha=64` の固定比較で、可視化しきい値の大まかな位置を推定
- 左右分割（16/64）で同一画像内比較し、端末条件差の影響を減らす
- `512 + alpha255 + 高輝度パッチ` で、512黒化が全体輝度不足由来かを切り分ける

## 結論（暫定）

- 「iCCP/cicpだけで十分」とはまだ言えない
- 観測される白化/黒化には、透明度と実効輝度しきい値の影響が混在している
- 次段は、alpha中間値と高輝度パッチで**しきい値境界を直接観測**する方針とする
- 詳細な仮説更新は `docs/hypothesis-update-2026-03-07.md` を参照
