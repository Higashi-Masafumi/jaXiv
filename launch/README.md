# jaXiv launch assets

Product Hunt ローンチ用のブランド素材一式。

## 生成方法

SVG をソースとして、`sharp` + `png-to-ico` で PNG / ICO を生成しています。
再生成する場合：

```bash
mkdir -p /tmp/asset-gen && cd /tmp/asset-gen
npm init -y && npm install sharp png-to-ico
# render.js を /home/user/jaXiv/launch/render.js からコピー
node render.js
```

レンダラ本体は `launch/render.js` にコミット済み。

## ファイル

### `frontend/public/` （本番に乗る）
- `favicon.ico` — 16/32/48 マルチサイズ ICO
- `favicon.svg` — モダンブラウザ用のベクター favicon
- `site.webmanifest` — PWA / Android インストール用
- `brand/icon-{16,32,48,180,192,512}.png` — 各種 PNG
- `brand/og-image.png` — OG / Twitter カード 1200x630

### `launch/src/`  — SVG ソース
- `logo-mark.svg` — 詳細マーク（180px 以上で使用）
- `logo-mark-small.svg` — 簡略マーク（favicon 16/32/48 用）
- `logo-wordmark.svg` — ワードマーク
- `og-image.svg` — OG 画像のソース
- `gallery-{1-hero,2-translate,3-features}.svg` — PH Gallery 画像

### `launch/product-hunt/`
- `logo-240.png` — PH の Logo 欄用
- `thumbnail-240.png` — PH の Thumbnail 欄用
- `gallery-{1,2,3}-*.png` — PH の Gallery 欄用（最低1枚、推奨3〜5枚）
- `COPY.md` — ローンチコピー（EN/JP 両方）

### `launch/preview-*.png`
プレビュー専用。コミットしてもしなくても良い。

## ブランドカラー

- Primary: `#0284c7` (sky-600) — UI と同じ
- Gradient: `#0ea5e9 → #0369a1` (sky-500 → sky-700)
- Accent: `#dc2626` (red-600) — 日本語化の象徴

## ローンチ手順
`launch/product-hunt/COPY.md` のチェックリスト参照。
