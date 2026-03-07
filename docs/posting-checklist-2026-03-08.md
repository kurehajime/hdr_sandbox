# X Posting Checklist

- checklist_mode: diversified_round_robin
- batch_size: 10
- batch_family_cap: 2
- include_targeted_followups: true

## 0) Controls

| role | candidate | file | expected | result_observed | x_post_url | notes |
|---|---|---|---|---|---|---|
| glow | `success_like` | `candidate_success_like.png` | glows | TODO | TODO | latest=glows |
| not_glow | `fail_no_iccp` | `candidate_fail_no_iccp.png` | not_glows | TODO | TODO | latest=not_glows |

## 1) Batch candidates

| order | family | candidate | file | current_observed | current_url | result_observed | x_post_url | notes |
|---:|---|---|---|---|---|---|---|---|
| 1 | `cicp` | `probe_cicp_bt2020_pq` | `candidate_probe_cicp_bt2020_pq.png` | `todo` | TODO | TODO | TODO | TODO |
| 2 | `isoeff` | `probe_isoeff_triplet` | `candidate_probe_isoeff_triplet.png` | `todo` | TODO | TODO | TODO | TODO |
| 3 | `alpha` | `probe_alpha_16` | `candidate_probe_alpha_16.png` | `todo` | TODO | TODO | TODO | TODO |
| 4 | `luma` | `probe_luma_ladder_alpha255` | `candidate_probe_luma_ladder_alpha255.png` | `todo` | TODO | TODO | TODO | TODO |
| 5 | `size` | `probe_size_512_alpha255_bright_patch` | `candidate_probe_size_512_alpha255_bright_patch.png` | `todo` | TODO | TODO | TODO | TODO |
| 6 | `cicp` | `probe_cicp_bt2020_pq_limited` | `candidate_probe_cicp_bt2020_pq_limited.png` | `todo` | TODO | TODO | TODO | TODO |
| 7 | `alpha` | `probe_alpha_64` | `candidate_probe_alpha_64.png` | `todo` | TODO | TODO | TODO | TODO |
| 8 | `luma` | `probe_luma_ladder_alpha64` | `candidate_probe_luma_ladder_alpha64.png` | `todo` | TODO | TODO | TODO | TODO |
| 9 | `size` | `probe_size_512` | `candidate_probe_size_512.png` | `whiteout` | TODO | TODO | TODO | TODO |
| 10 | `cicp` | `probe_cicp_bt2020_pq_matrix_1` | `candidate_probe_cicp_bt2020_pq_matrix_1.png` | `todo` | TODO | TODO | TODO | TODO |

## 1b) Targeted follow-up packs

既存観測のトリガー条件に応じて、次に優先投稿する候補群。

### alpha_gradient_orientation_followup

- reason: `probe_alpha_gradient` が mixed のため、向き変更(RL/TB)でalpha依存と位置バイアスを切り分ける

| candidate | file | current_observed | current_url | result_observed | x_post_url | notes |
|---|---|---|---|---|---|---|
| `probe_alpha_gradient_rl` | `candidate_probe_alpha_gradient_rl.png` | `todo` | TODO | TODO | TODO | TODO |
| `probe_alpha_gradient_tb` | `candidate_probe_alpha_gradient_tb.png` | `todo` | TODO | TODO | TODO | TODO |

### size_512_brightness_recovery_followup

- reason: `probe_size_512` と `probe_size_512_nontransparent` が非決定結果のため、bright patch条件で輝度不足由来かを検証する

| candidate | file | current_observed | current_url | result_observed | x_post_url | notes |
|---|---|---|---|---|---|---|
| `probe_size_512_alpha255_bright_patch` | `candidate_probe_size_512_alpha255_bright_patch.png` | `todo` | TODO | TODO | TODO | TODO |

### alpha_floor_threshold_followup

- reason: 低alpha(0/1)が非決定結果のため、16/64と左右同時比較で可視しきい値帯を絞り込む

| candidate | file | current_observed | current_url | result_observed | x_post_url | notes |
|---|---|---|---|---|---|---|
| `probe_alpha_16` | `candidate_probe_alpha_16.png` | `todo` | TODO | TODO | TODO | TODO |
| `probe_alpha_64` | `candidate_probe_alpha_64.png` | `todo` | TODO | TODO | TODO | TODO |
| `probe_alpha_lr_split_16_64` | `candidate_probe_alpha_lr_split_16_64.png` | `todo` | TODO | TODO | TODO | TODO |

## 2) Post-run notes

- controls_passed: TODO
- environment_notes: TODO
- follow_up_action: TODO
