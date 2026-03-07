# Candidate Comparison (auto-generated)

| name | file | bit_depth | color_type | iCCP | cicp | match_target_profile |
|---|---|---:|---:|---|---|---|
| success_like | `candidate_success_like.png` | 16 | 6 | yes | [9, 16, 0, 1] | YES |
| fail_8bit | `candidate_fail_8bit.png` | 8 | 6 | yes | [9, 16, 0, 1] | NO |
| fail_no_iccp | `candidate_fail_no_iccp.png` | 16 | 6 | no | - | NO |
| fail_rgb_no_alpha | `candidate_fail_rgb_no_alpha.png` | 16 | 2 | yes | [9, 16, 0, 1] | NO |

判定ロジック: `bit_depth=16` かつ `color_type=6(RGBA)` かつ `iCCP.cicp=[9,16,0,1]`