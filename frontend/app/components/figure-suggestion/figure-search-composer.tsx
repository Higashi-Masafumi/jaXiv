import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { SparklesIcon } from 'lucide-react'

import { Badge } from '~/components/ui/badge'
import { Button } from '~/components/ui/button'
import { Textarea } from '~/components/ui/textarea'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormMessage,
} from '~/components/ui/form'

const figureQuerySchema = z.object({
  query: z
    .string()
    .trim()
    .min(4, '作りたい図や研究内容をもう少し詳しく入力してください'),
})

type FigureQueryValues = z.infer<typeof figureQuerySchema>

const EXAMPLE_PROMPTS = [
  'Transformer のアーキテクチャ図',
  '強化学習の報酬カーブのグラフ',
  'アブレーション結果の比較表',
  '提案手法の全体像を示す概要図',
  'データ処理パイプラインのフロー図',
] as const

type FigureSearchComposerProps = {
  isLoading: boolean
  onSubmit: (query: string) => void
}

export function FigureSearchComposer({
  isLoading,
  onSubmit,
}: FigureSearchComposerProps) {
  const form = useForm<FigureQueryValues>({
    resolver: zodResolver(figureQuerySchema),
    defaultValues: { query: '' },
  })

  function handleSubmit(values: FigureQueryValues) {
    onSubmit(values.query)
  }

  return (
    <div className="flex w-full flex-col items-center gap-5">
      <div className="space-y-4 text-center">
        <p className="mx-auto flex w-fit items-center gap-1.5 rounded-full border border-hero-accent/30 bg-hero-accent/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-hero-accent">
          <SparklesIcon className="size-3.5" />
          Figure Inspiration
        </p>
        <h1 className="text-4xl font-black tracking-tight sm:text-5xl">
          図面提案
        </h1>
        <p className="mx-auto max-w-xl text-base leading-relaxed text-hero-muted sm:text-lg">
          作りたい図や研究内容を入力すると、AI
          が検索クエリを組み立て、論文全体から参考になる図を探します。
        </p>
      </div>

      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(handleSubmit)}
          className="w-full rounded-2xl border border-hero-card-border/70 bg-hero-card/80 p-5 shadow-2xl backdrop-blur-sm sm:p-6"
        >
          <FormField
            control={form.control}
            name="query"
            render={({ field }) => (
              <FormItem>
                <FormControl>
                  <Textarea
                    placeholder="例: グラフニューラルネットワークで分子の性質を予測する手法の全体像を示す図がほしい"
                    rows={3}
                    disabled={isLoading}
                    className="resize-none border-input bg-background text-foreground placeholder:text-muted-foreground"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <Button
            type="submit"
            disabled={isLoading}
            className="mt-3 w-full bg-hero-accent font-semibold text-primary-foreground transition-colors hover:bg-hero-accent/90 sm:w-44"
          >
            {isLoading ? '検索中...' : '図を探す'}
          </Button>
        </form>
      </Form>

      <div className="flex flex-wrap items-center justify-center gap-2">
        {EXAMPLE_PROMPTS.map(prompt => (
          <Badge
            key={prompt}
            variant="outline"
            asChild
            className="cursor-pointer border-hero-card-border/70 bg-hero-card/50 px-3 py-1 text-hero-muted transition-colors hover:border-hero-accent/50 hover:text-hero-foreground"
          >
            <button
              type="button"
              disabled={isLoading}
              onClick={() => {
                form.setValue('query', prompt, { shouldValidate: true })
              }}
            >
              {prompt}
            </button>
          </Badge>
        ))}
      </div>
    </div>
  )
}
