# success_sample.png 再現候補の生成手順（第13版）

更新日: 2026-03-08 (v13: 観測衝突/再試行候補の自動抽出を追加)

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
   - `candidate_probe_alpha_ladder_1_255.png`（新規・alpha段階バー）
   - `candidate_probe_luma_ladder_alpha255.png`（新規・RGB段階バー、alpha=255固定）
   - `candidate_probe_luma_ladder_alpha64.png`（新規・RGB段階バー、alpha=64固定）
   - `candidate_probe_alpha_luma_matrix.png`（新規・2Dマトリクス、x=alpha / y=luma）
   - `candidate_probe_isoeff_triplet.png`（新規・3段の目標effective固定帯）
   - `candidate_probe_threshold_zoom_matrix.png`（新規・しきい値近傍の密サンプリング2Dマトリクス）
   - `candidate_probe_cicp_bt2020_pq.png`（新規・cicp比較の基準）
   - `candidate_probe_cicp_bt2020_srgb.png`（新規・transfer差分）
   - `candidate_probe_cicp_bt709_pq.png`（新規・primaries差分）
   - `candidate_probe_cicp_bt709_srgb.png`（新規・primaries+transfer差分）
   - `candidate_probe_cicp_bt2020_pq_limited.png`（新規・range差分）
   - `candidate_probe_cicp_bt2020_pq_matrix_1.png`（新規・matrix差分）
   - `candidate_probe_size_512.png`
   - `candidate_probe_size_512_nontransparent.png`
   - `candidate_probe_size_512_alpha255_bright_patch.png`（新規）
5. 比較レポート `generated/comparison.md` を出力
6. 人間観測テンプレート `generated/human_observations_template.md` を出力（`--extended`時）

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

- 最新の追記先: `docs/human-observations.md`
- 運用ルール: 人間からの新規観測は `docs/hypothesis-update-2026-03-07.md` ではなく、必ず上記ファイルに追記する
- 人間観測から得た設計インプット（`docs/human-observations.md` 由来）:
  - `fail_no_iccp = not_glows`（iCCP/cicpの寄与を示唆）
  - `probe_alpha_gradient = mixed`（右のみ光る）
  - `probe_alpha_1 = whiteout` / `probe_size_512_nontransparent = blackout`（表示しきい値近傍の非線形）
- 整合性チェック:

```bash
python3 scripts/check_human_observations.py \
  --observations docs/human-observations.md \
  --generated-dir generated
```

- 2026-03-08 追加:
  - `pending_rows`（未投稿/URL未反映）と `missing_in_table`（generatedに存在するが観測表未登録）を同時に検出
  - `conflicting_candidates`（同一candidateの decisive 観測衝突）を検出
  - `retry_candidates`（最新が whiteout/blackout/mixed）を抽出
  - `--report-out docs/observation-status-YYYY-MM-DD.md` で次の投稿計画レポートを自動生成
  - `--strict-conflict` で再現性衝突をCI失敗扱いにできる

```bash
python3 scripts/check_human_observations.py \
  --observations docs/human-observations.md \
  --generated-dir generated \
  --report-out docs/observation-status-2026-03-08.md
```

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

- 最優先: `cicp_variant` 6条件を同一端末・同一表示条件で連続投稿し、transfer/primaries/range/matrix寄与を分離
  - 進捗確認は `docs/observation-status-2026-03-08.md` の pending セクションを参照
- `alpha=16` と `alpha=64` の固定比較で、可視化しきい値の大まかな位置を推定
- 左右分割（16/64）で同一画像内比較し、端末条件差の影響を減らす
- `512 + alpha255 + 高輝度パッチ` で、512黒化が全体輝度不足由来かを切り分ける
- `alpha_ladder_1_255` で、どのalpha laneから光り始めるかを1枚で観測する
  - lane定義は `generated/alpha_ladder_spec.md` を参照
- `luma_ladder_alpha255` / `luma_ladder_alpha64` で、alpha固定下の実効輝度しきい値を観測する
  - lane定義は `generated/luma_ladder_spec.md` を参照
  - しきい値laneが alpha=64 側で右にずれれば、「alpha×輝度」の積モデルを支持
- `alpha_luma_matrix` で、1枚内の2D境界（どのセルから光るか）を観測する
  - lane定義は `generated/alpha_luma_matrix_spec.md` を参照
  - 境界が左下→右上に出れば、`alpha×輝度` 積モデルを支持
- `isoeff_triplet` で、3行の目標effective（低/中/高）を比較する
  - lane定義は `generated/isoeff_triplet_spec.md` を参照
  - 各行が横方向に均一なら、積モデル優勢の根拠が強まる
- `threshold_zoom_matrix` で、alpha≈24 近傍の境界線を高密度に追跡する
  - lane定義は `generated/threshold_zoom_matrix_spec.md` を参照
  - 境界の折れ曲がり/段差が出るなら、alpha固有の非線形要因を疑う
- `cicp_variant` 6条件で、同一ピクセル時の transfer / primaries / range / matrix 寄与を切り分ける
  - 定義は `generated/cicp_variant_spec.md` を参照
  - `bt2020_pq -> bt2020_srgb` で変化すれば transfer 寄与が強い
  - `bt2020_pq -> bt709_pq` で変化すれば primaries 寄与が強い
  - `bt2020_pq -> bt2020_pq_limited` で変化すれば range 寄与が強い
  - `bt2020_pq -> bt2020_pq_matrix_1` で変化すれば matrix 寄与が強い

## 結論（暫定）

- 「iCCP/cicpだけで十分」とはまだ言えない
- 観測される白化/黒化には、透明度と実効輝度しきい値の影響が混在している
- 次段は、alpha/luma 2Dマトリクス + iso-effective triplet + threshold zoom matrix に加え cicp variant を使い、**境界形状と積モデルの均一性／局所非線形／cicp属性寄与**を同時観測する方針とする
- 詳細な仮説更新は `docs/hypothesis-update-2026-03-07.md` を参照
