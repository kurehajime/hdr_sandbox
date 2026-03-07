# Human Observation Status Report

- total_rows: 29
- unique_candidates: 29
- pending_rows: 21
- conflicting_candidates: 0
- retry_candidates: 5
- missing_in_table: 0

## Family progress (latest per candidate)

| family | candidates | resolved(glows/not_glows) | uncertain(mixed/whiteout/blackout) | todo_or_url_todo | completion |
|---|---:|---:|---:|---:|---:|
| `cicp` | 6 | 0 | 0 | 6 | 0.0% |
| `threshold` | 1 | 1 | 0 | 0 | 100.0% |
| `isoeff` | 1 | 0 | 0 | 1 | 0.0% |
| `alpha` | 11 | 1 | 3 | 9 | 9.1% |
| `luma` | 2 | 0 | 0 | 2 | 0.0% |
| `size` | 3 | 0 | 2 | 3 | 0.0% |
| `probe_other` | 1 | 1 | 0 | 0 | 100.0% |
| `success` | 1 | 1 | 0 | 0 | 100.0% |
| `fail` | 3 | 3 | 0 | 0 | 100.0% |

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
| `probe_cicp_bt2020_pq_limited` | `candidate_probe_cicp_bt2020_pq_limited.png` | `todo` | TODO |
| `probe_cicp_bt2020_pq_matrix_1` | `candidate_probe_cicp_bt2020_pq_matrix_1.png` | `todo` | TODO |
| `probe_cicp_bt2020_srgb` | `candidate_probe_cicp_bt2020_srgb.png` | `todo` | TODO |
| `probe_cicp_bt709_pq` | `candidate_probe_cicp_bt709_pq.png` | `todo` | TODO |
| `probe_cicp_bt709_srgb` | `candidate_probe_cicp_bt709_srgb.png` | `todo` | TODO |

### isoeff

| candidate | file | observed | x_post_url |
|---|---|---|---|
| `probe_isoeff_triplet` | `candidate_probe_isoeff_triplet.png` | `todo` | TODO |

### alpha

| candidate | file | observed | x_post_url |
|---|---|---|---|
| `probe_alpha_16` | `candidate_probe_alpha_16.png` | `todo` | TODO |
| `probe_alpha_64` | `candidate_probe_alpha_64.png` | `todo` | TODO |
| `probe_alpha_gradient_rl` | `candidate_probe_alpha_gradient_rl.png` | `todo` | TODO |
| `probe_alpha_gradient_tb` | `candidate_probe_alpha_gradient_tb.png` | `todo` | TODO |
| `probe_alpha_ladder_1_255` | `candidate_probe_alpha_ladder_1_255.png` | `todo` | TODO |
| `probe_alpha_lr_split_16_64` | `candidate_probe_alpha_lr_split_16_64.png` | `todo` | TODO |
| `probe_alpha_luma_matrix` | `candidate_probe_alpha_luma_matrix.png` | `todo` | TODO |
| `probe_alpha_0` | `candidate_probe_alpha_0.png` | `whiteout` | TODO |
| `probe_alpha_1` | `candidate_probe_alpha_1.png` | `whiteout` | TODO |

### luma

| candidate | file | observed | x_post_url |
|---|---|---|---|
| `probe_luma_ladder_alpha255` | `candidate_probe_luma_ladder_alpha255.png` | `todo` | TODO |
| `probe_luma_ladder_alpha64` | `candidate_probe_luma_ladder_alpha64.png` | `todo` | TODO |

### size

| candidate | file | observed | x_post_url |
|---|---|---|---|
| `probe_size_512_alpha255_bright_patch` | `candidate_probe_size_512_alpha255_bright_patch.png` | `todo` | TODO |
| `probe_size_512` | `candidate_probe_size_512.png` | `whiteout` | TODO |
| `probe_size_512_nontransparent` | `candidate_probe_size_512_nontransparent.png` | `blackout` | TODO |

## Suggested immediate batch

### 0) 端末状態確認用コントロール

- glow control: `candidate_success_like.png` (`success_like` / latest=glows)
- not_glow control: `candidate_fail_no_iccp.png` (`fail_no_iccp` / latest=not_glows)

### 1) 次バッチ候補（最大 10 件）

選定順: 未観測(todo/TODO) → 再試行(whiteout/blackout/mixed) → URL補完のみ（同一family上限=2）

- `candidate_probe_cicp_bt2020_pq.png` (probe_cicp_bt2020_pq / observed=todo / url=TODO)
- `candidate_probe_cicp_bt2020_pq_limited.png` (probe_cicp_bt2020_pq_limited / observed=todo / url=TODO)
- `candidate_probe_isoeff_triplet.png` (probe_isoeff_triplet / observed=todo / url=TODO)
- `candidate_probe_alpha_16.png` (probe_alpha_16 / observed=todo / url=TODO)
- `candidate_probe_alpha_64.png` (probe_alpha_64 / observed=todo / url=TODO)
- `candidate_probe_luma_ladder_alpha255.png` (probe_luma_ladder_alpha255 / observed=todo / url=TODO)
- `candidate_probe_luma_ladder_alpha64.png` (probe_luma_ladder_alpha64 / observed=todo / url=TODO)
- `candidate_probe_size_512_alpha255_bright_patch.png` (probe_size_512_alpha255_bright_patch / observed=todo / url=TODO)
- `candidate_probe_size_512.png` (probe_size_512 / observed=whiteout / url=TODO)
- `candidate_probe_cicp_bt2020_pq_matrix_1.png` (probe_cicp_bt2020_pq_matrix_1 / observed=todo / url=TODO)

### 1b) 次バッチ候補（多様性重視・family round-robin / 最大 10 件）

端末状態のドリフトを疑う場合、同一family連投を避けて候補を分散する。

- `candidate_probe_cicp_bt2020_pq.png` (probe_cicp_bt2020_pq / family=cicp / observed=todo / url=TODO)
- `candidate_probe_isoeff_triplet.png` (probe_isoeff_triplet / family=isoeff / observed=todo / url=TODO)
- `candidate_probe_alpha_16.png` (probe_alpha_16 / family=alpha / observed=todo / url=TODO)
- `candidate_probe_luma_ladder_alpha255.png` (probe_luma_ladder_alpha255 / family=luma / observed=todo / url=TODO)
- `candidate_probe_size_512_alpha255_bright_patch.png` (probe_size_512_alpha255_bright_patch / family=size / observed=todo / url=TODO)
- `candidate_probe_cicp_bt2020_pq_limited.png` (probe_cicp_bt2020_pq_limited / family=cicp / observed=todo / url=TODO)
- `candidate_probe_alpha_64.png` (probe_alpha_64 / family=alpha / observed=todo / url=TODO)
- `candidate_probe_luma_ladder_alpha64.png` (probe_luma_ladder_alpha64 / family=luma / observed=todo / url=TODO)
- `candidate_probe_size_512.png` (probe_size_512 / family=size / observed=whiteout / url=TODO)
- `candidate_probe_cicp_bt2020_pq_matrix_1.png` (probe_cicp_bt2020_pq_matrix_1 / family=cicp / observed=todo / url=TODO)

### 2) cicp比較メモ

以下のcicp候補を同一端末・同一表示条件で連続投稿し、差分だけを比較する:
- `candidate_probe_cicp_bt2020_pq.png`
- `candidate_probe_cicp_bt2020_pq_limited.png`
- `candidate_probe_cicp_bt2020_pq_matrix_1.png`
- `candidate_probe_cicp_bt2020_srgb.png`
- `candidate_probe_cicp_bt709_pq.png`
- `candidate_probe_cicp_bt709_srgb.png`
