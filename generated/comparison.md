# Candidate Comparison (auto-generated)

| name | file | size | bit_depth | color_type | iCCP | cicp | legacy(16bit+RGBA+iCCP/cicp) | relaxed(iCCP/cicp only) |
|---|---|---|---:|---:|---|---|---|---|
| success_like | `candidate_success_like.png` | 400x400 | 16 | 6 | yes | [9, 16, 0, 1] | YES | YES |
| fail_8bit | `candidate_fail_8bit.png` | 400x400 | 8 | 6 | yes | [9, 16, 0, 1] | NO | YES |
| fail_no_iccp | `candidate_fail_no_iccp.png` | 400x400 | 16 | 6 | no | - | NO | NO |
| fail_rgb_no_alpha | `candidate_fail_rgb_no_alpha.png` | 400x400 | 16 | 2 | yes | [9, 16, 0, 1] | NO | YES |
| probe_8bit_rgb_no_alpha | `candidate_probe_8bit_rgb_no_alpha.png` | 400x400 | 8 | 2 | yes | [9, 16, 0, 1] | NO | YES |
| probe_alpha_255 | `candidate_probe_alpha_255.png` | 400x400 | 16 | 6 | yes | [9, 16, 0, 1] | YES | YES |
| probe_alpha_0 | `candidate_probe_alpha_0.png` | 400x400 | 16 | 6 | yes | [9, 16, 0, 1] | YES | YES |
| probe_alpha_1 | `candidate_probe_alpha_1.png` | 400x400 | 16 | 6 | yes | [9, 16, 0, 1] | YES | YES |
| probe_alpha_16 | `candidate_probe_alpha_16.png` | 400x400 | 16 | 6 | yes | [9, 16, 0, 1] | YES | YES |
| probe_alpha_64 | `candidate_probe_alpha_64.png` | 400x400 | 16 | 6 | yes | [9, 16, 0, 1] | YES | YES |
| probe_alpha_gradient | `candidate_probe_alpha_gradient.png` | 400x400 | 16 | 6 | yes | [9, 16, 0, 1] | YES | YES |
| probe_alpha_lr_split_16_64 | `candidate_probe_alpha_lr_split_16_64.png` | 400x400 | 16 | 6 | yes | [9, 16, 0, 1] | YES | YES |
| probe_alpha_ladder_1_255 | `candidate_probe_alpha_ladder_1_255.png` | 400x400 | 16 | 6 | yes | [9, 16, 0, 1] | YES | YES |
| probe_luma_ladder_alpha255 | `candidate_probe_luma_ladder_alpha255.png` | 400x400 | 16 | 6 | yes | [9, 16, 0, 1] | YES | YES |
| probe_luma_ladder_alpha64 | `candidate_probe_luma_ladder_alpha64.png` | 400x400 | 16 | 6 | yes | [9, 16, 0, 1] | YES | YES |
| probe_alpha_luma_matrix | `candidate_probe_alpha_luma_matrix.png` | 400x400 | 16 | 6 | yes | [9, 16, 0, 1] | YES | YES |
| probe_size_512 | `candidate_probe_size_512.png` | 512x512 | 16 | 6 | yes | [9, 16, 0, 1] | YES | YES |
| probe_size_512_nontransparent | `candidate_probe_size_512_nontransparent.png` | 512x512 | 16 | 6 | yes | [9, 16, 0, 1] | YES | YES |
| probe_size_512_alpha255_bright_patch | `candidate_probe_size_512_alpha255_bright_patch.png` | 512x512 | 16 | 6 | yes | [9, 16, 0, 1] | YES | YES |

判定ロジック:
- legacy: `bit_depth=16` かつ `color_type=6(RGBA)` かつ `iCCP.cicp=[9,16,0,1]`
- relaxed: `iCCP.cicp=[9,16,0,1]`（bit depth / alpha / size は不問）

extended候補の狙い:
- `probe_8bit_rgb_no_alpha`: 8bit と no-alpha を同時適用（2x2切り分けの第4点）
- `probe_alpha_255` / `probe_alpha_0`: alpha=255 と alpha=0 の極端条件を比較
- `probe_alpha_1` / `probe_alpha_16` / `probe_alpha_64`: 極小alpha域の表示しきい値を探索
- `probe_alpha_gradient`: alphaを1..65535で連続変化（alpha依存の境界を観測）
- `probe_alpha_lr_split_16_64`: 左右分割（左alpha=16 / 右alpha=64）で見え方を即比較
- `probe_alpha_ladder_1_255`: alpha段階(1..255)の縦バーで発光しきい値の概算を1枚で観測
- `probe_luma_ladder_alpha255` / `probe_luma_ladder_alpha64`: RGB段階バー（alpha固定）で実効輝度しきい値を探索
- `probe_alpha_luma_matrix`: 2Dグリッド（x=alpha, y=luma）でしきい値境界形状を1枚で観測
- `probe_size_512`: 512化のみ（従来観測の再確認）
- `probe_size_512_nontransparent`: 512 + alpha=255固定（サイズ要因と透明要因の切り分け）
- `probe_size_512_alpha255_bright_patch`: 512 + alpha=255 + 右側高輝度パッチ（実効輝度しきい値を確認）