# Human Observation Status Report

- total_rows: 27
- unique_candidates: 27
- pending_rows: 19
- conflicting_candidates: 0
- retry_candidates: 5
- missing_in_table: 0

## Retry candidates (non-decisive latest result)

最新が whiteout/blackout/mixed の候補。判定可能な条件で再投稿する。

| candidate | file | latest_observed | attempts | latest_url |
|---|---|---|---:|---|
| `probe_alpha_0` | `candidate_probe_alpha_0.png` | `whiteout` | 1 | TODO |
| `probe_alpha_1` | `candidate_probe_alpha_1.png` | `whiteout` | 1 | TODO |
| `probe_alpha_gradient` | `candidate_probe_alpha_gradient.png` | `mixed` | 1 | https://x.com/kurehajime/status/2030244873153175737 |
| `probe_size_512` | `candidate_probe_size_512.png` | `whiteout` | 1 | TODO |
| `probe_size_512_nontransparent` | `candidate_probe_size_512_nontransparent.png` | `blackout` | 1 | TODO |

## Pending candidates (needs X posting / result entry)

優先順の目安: cicp → threshold/isoeff → alpha/luma → その他

### cicp

| candidate | file | observed | x_post_url |
|---|---|---|---|
| `probe_cicp_bt2020_pq` | `candidate_probe_cicp_bt2020_pq.png` | `todo` | TODO |
| `probe_cicp_bt2020_srgb` | `candidate_probe_cicp_bt2020_srgb.png` | `todo` | TODO |
| `probe_cicp_bt709_pq` | `candidate_probe_cicp_bt709_pq.png` | `todo` | TODO |
| `probe_cicp_bt709_srgb` | `candidate_probe_cicp_bt709_srgb.png` | `todo` | TODO |
| `probe_cicp_bt2020_pq_limited` | `candidate_probe_cicp_bt2020_pq_limited.png` | `todo` | TODO |
| `probe_cicp_bt2020_pq_matrix_1` | `candidate_probe_cicp_bt2020_pq_matrix_1.png` | `todo` | TODO |

### alpha

| candidate | file | observed | x_post_url |
|---|---|---|---|
| `probe_alpha_0` | `candidate_probe_alpha_0.png` | `whiteout` | TODO |
| `probe_alpha_1` | `candidate_probe_alpha_1.png` | `whiteout` | TODO |
| `probe_alpha_16` | `candidate_probe_alpha_16.png` | `todo` | TODO |
| `probe_alpha_64` | `candidate_probe_alpha_64.png` | `todo` | TODO |
| `probe_alpha_lr_split_16_64` | `candidate_probe_alpha_lr_split_16_64.png` | `todo` | TODO |
| `probe_alpha_ladder_1_255` | `candidate_probe_alpha_ladder_1_255.png` | `todo` | TODO |
| `probe_alpha_luma_matrix` | `candidate_probe_alpha_luma_matrix.png` | `todo` | TODO |

### isoeff

| candidate | file | observed | x_post_url |
|---|---|---|---|
| `probe_isoeff_triplet` | `candidate_probe_isoeff_triplet.png` | `todo` | TODO |

### luma

| candidate | file | observed | x_post_url |
|---|---|---|---|
| `probe_luma_ladder_alpha255` | `candidate_probe_luma_ladder_alpha255.png` | `todo` | TODO |
| `probe_luma_ladder_alpha64` | `candidate_probe_luma_ladder_alpha64.png` | `todo` | TODO |

### size

| candidate | file | observed | x_post_url |
|---|---|---|---|
| `probe_size_512` | `candidate_probe_size_512.png` | `whiteout` | TODO |
| `probe_size_512_nontransparent` | `candidate_probe_size_512_nontransparent.png` | `blackout` | TODO |
| `probe_size_512_alpha255_bright_patch` | `candidate_probe_size_512_alpha255_bright_patch.png` | `todo` | TODO |

## Suggested immediate batch

以下の6条件(cicp)を同一端末・同一表示条件で連続投稿して比較する:
- `candidate_probe_cicp_bt2020_pq.png`
- `candidate_probe_cicp_bt2020_srgb.png`
- `candidate_probe_cicp_bt709_pq.png`
- `candidate_probe_cicp_bt709_srgb.png`
- `candidate_probe_cicp_bt2020_pq_limited.png`
- `candidate_probe_cicp_bt2020_pq_matrix_1.png`
