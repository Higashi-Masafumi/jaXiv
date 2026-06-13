import type { LucideIcon } from 'lucide-react'

export function GenerationHero({
  icon: Icon,
  badge,
  titleLead,
  titleHighlight,
  description,
  children,
}: {
  icon: LucideIcon
  badge: string
  titleLead: string
  titleHighlight: string
  description: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <div className="relative overflow-hidden bg-gradient-to-br from-indigo-50/80 via-background to-violet-50/60 px-4 pb-10 pt-12 dark:from-indigo-950/20 dark:to-violet-950/20 sm:px-6 sm:pt-16">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 overflow-hidden"
      >
        <div className="absolute -right-32 -top-32 h-72 w-72 rounded-full bg-indigo-200/30 blur-3xl dark:bg-indigo-500/10" />
        <div className="absolute -left-16 bottom-0 h-56 w-56 rounded-full bg-violet-200/25 blur-3xl dark:bg-violet-500/10" />
      </div>

      <div className="relative mx-auto w-full max-w-3xl">
        <div className="mb-5 flex justify-center sm:justify-start">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary/8 px-3 py-1 text-xs font-medium text-primary">
            <Icon className="size-3" />
            {badge}
          </span>
        </div>

        <h1 className="text-center text-3xl font-black leading-tight tracking-tight text-foreground sm:text-left sm:text-4xl lg:text-5xl">
          {titleLead}
          <br className="hidden sm:block" />
          <span className="bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">
            {titleHighlight}
          </span>
        </h1>

        <p className="mt-3 text-center text-sm leading-relaxed text-muted-foreground sm:text-left sm:text-base">
          {description}
        </p>

        {children}
      </div>
    </div>
  )
}
