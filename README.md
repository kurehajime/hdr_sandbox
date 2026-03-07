# hdr_sandbox

X向けHDR画像投稿の再現調査リポジトリ。

## 現在の成果

- 成功例 `IMG_0892.PNG` の実ファイル解析を実施
- 判明した特徴:
  - PNG / 400x400 / 16bit / RGBA(Color Type 6)
  - iCCPあり
  - ICC内 `cicp = [9,16,0,1]` (BT.2020 + PQ)

詳細は `docs/success-case-IMG_0892.md` を参照。

## 検証スクリプト

### 1) PNGプロファイル確認

```bash
python3 scripts/check_png_hdr.py path/to/image.png
```

出力例:

- IHDR情報（解像度、bit depth、color type）
- iCCPの有無
- ICC内cicp値
- 成功プロファイル一致判定 (`match_target_profile`)

### 2) 再現候補の一括生成（成功/失敗比較）

```bash
python3 scripts/make_candidates.py \
  --input sample/success_sample.png \
  --success-ref sample/success_sample.png \
  --outdir generated \
  --extended
```

出力（基本 + 追加切り分け候補）:

- `generated/candidate_success_like.png`
- `generated/candidate_fail_8bit.png`
- `generated/candidate_fail_no_iccp.png`
- `generated/candidate_fail_rgb_no_alpha.png`
- `generated/candidate_probe_8bit_rgb_no_alpha.png`
- `generated/candidate_probe_alpha_255.png`
- `generated/candidate_probe_alpha_0.png`
- `generated/candidate_probe_alpha_1.png`
- `generated/candidate_probe_alpha_16.png`
- `generated/candidate_probe_alpha_64.png`
- `generated/candidate_probe_alpha_gradient.png`
- `generated/candidate_probe_alpha_lr_split_16_64.png`
- `generated/candidate_probe_alpha_ladder_1_255.png`
- `generated/candidate_probe_luma_ladder_alpha255.png`
- `generated/candidate_probe_luma_ladder_alpha64.png`
- `generated/candidate_probe_alpha_luma_matrix.png`
- `generated/candidate_probe_isoeff_triplet.png`
- `generated/candidate_probe_threshold_zoom_matrix.png`
- `generated/candidate_probe_cicp_bt2020_pq.png`
- `generated/candidate_probe_cicp_bt2020_srgb.png`
- `generated/candidate_probe_cicp_bt709_pq.png`
- `generated/candidate_probe_cicp_bt709_srgb.png`
- `generated/candidate_probe_cicp_bt2020_pq_limited.png`
- `generated/candidate_probe_cicp_bt2020_pq_matrix_1.png`
- `generated/candidate_probe_size_512.png`
- `generated/candidate_probe_size_512_nontransparent.png`
- `generated/candidate_probe_size_512_alpha255_bright_patch.png`
- `generated/comparison.md`（比較表）
- `generated/alpha_ladder_spec.md`（alpha段階のlane対応表）
- `generated/luma_ladder_spec.md`（RGB段階と実効輝度のlane対応表）
- `generated/alpha_luma_matrix_spec.md`（2Dマトリクスの行列lane対応表）
- `generated/isoeff_triplet_spec.md`（目標effective固定帯のlane対応表）
- `generated/threshold_zoom_matrix_spec.md`（しきい値近傍マトリクスの行列lane対応表）
- `generated/cicp_variant_spec.md`（cicp比較6条件の対応表）
- `generated/human_observations_template.md`（人間観測の追記テンプレート）

### 3) 人間観測ログの整合性チェック

```bash
python3 scripts/check_human_observations.py \
  --observations docs/human-observations.md \
  --generated-dir generated
```

人間の追記を別ファイル（例: `docs/human-observations-extra.md`）へ分ける場合は、
`--observations-glob` で同時読込できる:

```bash
python3 scripts/check_human_observations.py \
  --observations docs/human-observations.md \
  --observations-glob 'human-observations-*.md' \
  --generated-dir generated
```

### 4) 未観測候補のレポート生成（次の投稿計画）

```bash
python3 scripts/check_human_observations.py \
  --observations docs/human-observations.md \
  --observations-glob 'human-observations-*.md' \
  --generated-dir generated \
  --report-out docs/observation-status-YYYY-MM-DD.md \
  --report-json-out docs/observation-status-YYYY-MM-DD.json \
  --batch-size 10
```

- `pending_rows`: 未投稿またはURL未反映の候補数
- `conflicting_candidates`: 同一candidateで `glows/not_glows/mixed` が衝突した候補数
- `retry_candidates`: 最新観測が `whiteout/blackout/mixed` の再検証候補数
- `missing_in_table`: generatedに存在するが観測表に未登録の候補数
- `observation_files`: チェック時に読み込んだ観測ファイル一覧（複数ファイル運用の確認用）
- `family_progress_latest`: candidate最新状態を family 別に集計（resolved/uncertain/todo_or_url_todo/completion）
- `--report-json-out`: pending/retry/conflict/推奨バッチをJSONで出力（自動投稿フロー連携用）
- レポートの `Suggested immediate batch` で、
  - 端末状態確認用コントロール（glow / not_glow）
  - 状態優先（未観測todo → 再試行whiteout/blackout/mixed → URL補完）+ 系統優先つきの次バッチ候補（`--batch-size`件）
  - 同一family連投を避ける `1b) 多様性重視バッチ`（round-robin）
  を自動提案
- `--strict-pending` を付けると pending が1件でも終了コード2
- `--strict-conflict` を付けると decisive観測の衝突が1件でも終了コード2

詳細は `docs/reproduction-candidates.md` / `docs/human-observations.md` /
`docs/hypothesis-update-2026-03-07.md` を参照。
