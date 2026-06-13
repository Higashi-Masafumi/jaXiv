import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

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
    <div className="flex w-full max-w-3xl flex-col gap-3">
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(handleSubmit)}
          className="rounded-xl border border-border bg-card p-4 shadow-sm"
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
                    className="resize-none"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <Button
            type="submit"
            disabled={isLoading || disabled}
            className="mt-3 w-full sm:w-44"
          >
            {isLoading ? '検索中...' : '図を探す'}
          </Button>
        </form>
      </Form>

      <div className="flex flex-wrap items-center gap-2">
        {EXAMPLE_PROMPTS.map(prompt => (
          <Badge
            key={prompt}
            variant="outline"
            asChild
            className="cursor-pointer bg-muted/40 px-3 py-1 text-muted-foreground transition-colors hover:border-primary/50 hover:text-foreground"
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
