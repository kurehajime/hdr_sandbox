# Human Observations

人間がX投稿で確認した見え方の記録。
**追記はこのファイルに集約**し、`docs/hypothesis-update-2026-03-07.md` は仮説整理用として使う。

| candidate | file | observed | x_post_url | notes |
|---|---|---|---|---|
| success_like | `candidate_success_like.png` | glows | https://x.com/kurehajime/status/2030233227521302817 | 光って見えた |
| fail_rgb_no_alpha | `candidate_fail_rgb_no_alpha.png` | glows | https://x.com/kurehajime/status/2030233123523547149 | 光って見えた |
| fail_no_iccp | `candidate_fail_no_iccp.png` | not_glows | https://x.com/kurehajime/status/2030232947044110346 | 光って見えない |
| fail_8bit | `candidate_fail_8bit.png` | glows | https://x.com/kurehajime/status/2030232680877723982 | 光って見えた |
| probe_8bit_rgb_no_alpha | `candidate_probe_8bit_rgb_no_alpha.png` | glows | https://x.com/kurehajime/status/2030240958701568112 | 光って見えた |
| probe_alpha_255 | `candidate_probe_alpha_255.png` | glows | https://x.com/kurehajime/status/2030241207994159531 | 光って見えた |
| probe_alpha_0 | `candidate_probe_alpha_0.png` | whiteout | TODO | 真っ白でなにも見えず |
| probe_size_512 | `candidate_probe_size_512.png` | whiteout | TODO | 真っ白でなにも見えず |
| probe_alpha_gradient | `candidate_probe_alpha_gradient.png` | mixed | https://x.com/kurehajime/status/2030244873153175737 | 右半分のみ光る。左半分は黒っぽく見える |
| probe_alpha_1 | `candidate_probe_alpha_1.png` | whiteout | TODO | 真っ白でなにも見えず |
| probe_size_512_nontransparent | `candidate_probe_size_512_nontransparent.png` | blackout | TODO | 真っ黒でなにも見えず |
| probe_cicp_bt2020_pq | `candidate_probe_cicp_bt2020_pq.png` | todo | TODO | 新規: cicp比較の基準（既存alpha=64相当） |
| probe_cicp_bt2020_srgb | `candidate_probe_cicp_bt2020_srgb.png` | todo | TODO | 新規: transferのみPQ→sRGBに変更 |
| probe_cicp_bt709_pq | `candidate_probe_cicp_bt709_pq.png` | todo | TODO | 新規: primariesのみBT.2020→BT.709に変更 |
| probe_cicp_bt709_srgb | `candidate_probe_cicp_bt709_srgb.png` | todo | TODO | 新規: primaries+transfer同時変更 |
| probe_cicp_bt2020_pq_limited | `candidate_probe_cicp_bt2020_pq_limited.png` | todo | TODO | 新規: rangeのみFull→Limitedに変更 |
| probe_cicp_bt2020_pq_matrix_1 | `candidate_probe_cicp_bt2020_pq_matrix_1.png` | todo | TODO | 新規: matrixのみ0→1に変更 |

## observed 値の凡例

- `glows`: 光って見える
- `not_glows`: 光って見えない
- `whiteout`: 真っ白で評価不能
- `blackout`: 真っ黒で評価不能
- `mixed`: 部分的に光る/条件依存

## 追記ルール

- 新しい投稿結果はこの表に1行追加
- 同一candidateを再投稿した場合は、新しい行を下に追加（時系列を保持）
- `x_post_url` が未取得なら `TODO` とし、後で置換
