# jaXiv — Product Hunt launch copy

すべての文字数は Product Hunt フォーム制限に合わせて調整済み。
英語が一次素材（PH本体）、日本語は X / Slack / 社内告知用。

---

## English (primary)

### Name
jaXiv

### Tagline  *(max 60 chars)*
> Read arXiv papers in Japanese — layout intact.  *(48 chars)*

代替案:
- `Translate arXiv papers to Japanese, layout preserved.` (54)
- `arXiv papers, recompiled in Japanese.` (38)

### Description  *(max 260 chars)*
> Paste an arXiv URL and jaXiv recompiles the LaTeX into a clean Japanese PDF — figures, equations and citations stay exactly where they were. Then chat with the paper or publish your reading notes as a shareable blog. Built for researchers who read fast.  *(259 chars)*

### Topics / Tags
`Productivity` `Education` `Artificial Intelligence` `Research` `Developer Tools` `Open Source`

### First comment (maker comment)
> Hey Product Hunt 👋
>
> I'm the maker of **jaXiv**. I built it because reading English ML/physics papers in Japanese — without losing the layout — was something every researcher I know complained about. Existing translators give you a wall of text. The figures, the equations, the references — gone.
>
> jaXiv takes a different approach:
>
> 1. **Paste an arXiv URL.** We pull the LaTeX source, not the PDF.
> 2. **Translate at the source level.** Then recompile with LaTeX — your figures, math, bibliography all survive.
> 3. **Chat with the paper.** Ask "what does this equation mean?" in Japanese, scoped to the section you're reading.
> 4. **Turn it into a blog.** Share your reading notes with your lab or on social in Zenn-style Markdown.
>
> The whole pipeline is open source. We use Supabase for auth/storage, FastAPI + LaTeX on the backend, and a separate PDF-analysis service for layout-aware chunking.
>
> Would love feedback — especially on edge cases (broken bibtex, non-arXiv preprints, etc). I'm in the comments all day. 🙌

---

## 日本語 (X / Slack / Zenn 用)

### キャッチコピー
> arXiv の論文を、レイアウトを保ったまま日本語で読む。

### ショート紹介（〜140字）
> arXiv の URL を貼るだけで、論文を日本語に。LaTeX を再コンパイルするから図・式・参考文献がズレません。読みながら日本語でチャット質問もでき、読書メモはそのままブログとしてシェアできます。研究を速く読むためのツールです。

### 詳細紹介（〜400字）
> jaXiv は、arXiv の英語論文を **レイアウトそのまま** 日本語化する翻訳サービスです。PDF を OCR して翻訳する従来型と違い、arXiv の LaTeX ソースに直接介入して翻訳・再コンパイルするので、図・数式・引用が崩れない日本語 PDF が得られます。
>
> さらに、PDF を解析してセクション単位でチャットできるので「この式の意味は？」を日本語で質問可能。読んだ論文はそのまま Zenn 風のブログ記事として研究室や SNS にシェアできます。
>
> 研究を速く読むための、もう一つのワークフローです。

### X (Twitter) ポスト案 — ローンチ当日
> 🚀 jaXiv を Product Hunt でローンチしました。
>
> arXiv の URL を貼るだけで、論文をレイアウトそのまま日本語に翻訳。LaTeX 再コンパイル方式なので、図・式・参考文献が崩れません。
>
> 読みながら日本語でチャット、ブログとしてシェアまで。
>
> 応援 → [PH URL]

### Slack / Discord 告知案
> 本日 Product Hunt で jaXiv をローンチしました 🎉
> arXiv 論文をレイアウトを保ったまま日本語化するツールです。研究室内で読み合わせするときに使ってもらえると嬉しいです。
> 投票・コメント大歓迎です → [PH URL]

---

## ローンチ前チェックリスト

- [ ] PH の Gallery に `gallery-1-hero.png` / `gallery-2-translate.png` / `gallery-3-features.png` をアップロード
- [ ] Logo に `logo-240.png`、Thumbnail に `thumbnail-240.png` を設定
- [ ] Tagline は半角 60 字以内であることを再確認（上の英語案は 48 字）
- [ ] Description は 260 字以内
- [ ] Maker comment はローンチ 0:01 (PST) 直後に投下
- [ ] OG 画像 (`/brand/og-image.png`) が本番ドメインで配信されているか https://www.opengraph.xyz/ で確認
- [ ] favicon が `/favicon.ico` `/favicon.svg` `/brand/icon-180.png` で 200 を返すか確認
- [ ] X / Slack / Discord / 研究室メーリス の同日告知文を予約投稿
