import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { LightbulbIcon, SearchIcon } from 'lucide-react'

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
  disabled?: boolean
  onSubmit: (query: string) => void
}

export function FigureSearchComposer({
  isLoading,
  disabled = false,
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
    <div className="flex w-full max-w-3xl flex-col gap-3.5">
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(handleSubmit)}
          className="rounded-2xl border border-border/80 bg-white/90 shadow-lg shadow-indigo-100/40 backdrop-blur-sm transition-[border-color,box-shadow] focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-primary/15 dark:bg-card/90 dark:shadow-none"
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
                    disabled={isLoading || disabled}
                    className="resize-none border-0 bg-transparent px-4 pt-4 pb-1 text-sm shadow-none focus-visible:ring-0 sm:text-base dark:bg-transparent"
                    onKeyDown={event => {
                      // Enter で送信、Shift+Enter で改行。IME 変換確定の Enter は無視する
                      if (
                        event.key === 'Enter' &&
                        !event.shiftKey &&
                        !event.nativeEvent.isComposing
                      ) {
                        event.preventDefault()
                        form.handleSubmit(handleSubmit)()
                      }
                    }}
                    {...field}
                  />
                </FormControl>
                <FormMessage className="px-4 pt-1 text-xs" />
              </FormItem>
            )}
          />

          <div className="flex items-center justify-between gap-3 px-3 pb-3 pt-1">
            <p className="hidden text-xs text-muted-foreground sm:block">
              Enter で検索 / Shift + Enter で改行
            </p>
            <Button
              type="submit"
              size="icon"
              aria-label="図を探す"
              disabled={isLoading || disabled}
              className="ml-auto size-10 rounded-full"
            >
              {isLoading ? (
                <span className="inline-block size-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
              ) : (
                <SearchIcon className="size-4" />
              )}
            </Button>
          </div>
        </form>
      </Form>

      <div className="flex flex-wrap items-center gap-2">
        <span className="inline-flex items-center gap-1 text-xs font-medium text-muted-foreground">
          <LightbulbIcon className="size-3.5" />
          例:
        </span>
        {EXAMPLE_PROMPTS.map(prompt => (
          <Badge
            key={prompt}
            variant="outline"
            asChild
            className="cursor-pointer rounded-full border-border/70 bg-white/60 px-3 py-1 font-normal text-muted-foreground backdrop-blur-sm transition-colors hover:border-primary/50 hover:bg-primary/5 hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50 dark:bg-card/60"
          >
            <button
              type="button"
              disabled={isLoading || disabled}
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
