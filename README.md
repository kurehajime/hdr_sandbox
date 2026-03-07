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

```bash
python3 scripts/check_png_hdr.py path/to/image.png
```

出力例:

- IHDR情報（解像度、bit depth、color type）
- iCCPの有無
- ICC内cicp値
- 成功プロファイル一致判定 (`match_target_profile`)
