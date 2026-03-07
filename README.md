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
- `generated/candidate_probe_size_512.png`
- `generated/candidate_probe_size_512_nontransparent.png`
- `generated/candidate_probe_size_512_alpha255_bright_patch.png`
- `generated/comparison.md`（比較表）
- `generated/alpha_ladder_spec.md`（alpha段階のlane対応表）
- `generated/luma_ladder_spec.md`（RGB段階と実効輝度のlane対応表）
- `generated/alpha_luma_matrix_spec.md`（2Dマトリクスの行列lane対応表）
- `generated/isoeff_triplet_spec.md`（目標effective固定帯のlane対応表）

詳細は `docs/reproduction-candidates.md` と
`docs/hypothesis-update-2026-03-07.md` を参照。
