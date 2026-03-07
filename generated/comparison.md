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
| probe_size_512 | `candidate_probe_size_512.png` | 512x512 | 16 | 6 | yes | [9, 16, 0, 1] | YES | YES |

判定ロジック:
- legacy: `bit_depth=16` かつ `color_type=6(RGBA)` かつ `iCCP.cicp=[9,16,0,1]`
- relaxed: `iCCP.cicp=[9,16,0,1]`（bit depth / alpha / size は不問）

extended候補の狙い:
- `probe_8bit_rgb_no_alpha`: 8bit と no-alpha を同時適用（2x2切り分けの第4点）
- `probe_alpha_255` / `probe_alpha_0`: alpha値そのものの寄与を確認
- `probe_size_512`: 400x400固定が必要かを確認