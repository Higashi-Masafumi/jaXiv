import { CheckIcon } from 'lucide-react'

import type { BlogStreamStep } from '~/hooks/use-blog-stream'

export function GenerationSteps({ steps }: { steps: BlogStreamStep[] }) {
  if (steps.length === 0) return null

  return (
    <ul className="mt-5 space-y-2">
      {steps.map((step, i) => (
        <li key={i} className="flex items-center gap-3">
          <span
            className={`flex size-5 shrink-0 items-center justify-center rounded-full transition-colors ${
              step.done
                ? 'bg-primary/15 text-primary'
                : 'bg-primary/8 text-primary'
            }`}
          >
            {step.done ? (
              <CheckIcon className="size-3 stroke-[2.5]" />
            ) : (
              <span className="inline-block size-2.5 animate-spin rounded-full border-[1.5px] border-primary border-t-transparent" />
            )}
          </span>
          <span
            className={`text-sm transition-colors ${
              step.done
                ? 'text-muted-foreground line-through decoration-muted-foreground/50'
                : 'font-medium text-foreground'
            }`}
          >
            {step.message}
          </span>
        </li>
      ))}
    </ul>
  )
}
