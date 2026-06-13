import {
  isRouteErrorResponse,
  Link,
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
} from 'react-router'
import { CompassIcon } from 'lucide-react'

import type { Route } from './+types/root'
import { AuthProvider } from '~/contexts/auth-context'
import { Button } from '~/components/ui/button'
import '~/lib/api-client'
import './app.css'
import 'zenn-content-css/lib/index.css'

export const links: Route.LinksFunction = () => [
  { rel: 'icon', type: 'image/png', sizes: '48x48', href: '/favicon-48.png' },
  { rel: 'icon', type: 'image/png', sizes: '32x32', href: '/favicon-32.png' },
  { rel: 'icon', type: 'image/png', sizes: '16x16', href: '/favicon-16.png' },
  { rel: 'apple-touch-icon', href: '/apple-touch-icon.png' },
  { rel: 'manifest', href: '/manifest.json' },
  { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
  {
    rel: 'preconnect',
    href: 'https://fonts.gstatic.com',
    crossOrigin: 'anonymous',
  },
  {
    rel: 'stylesheet',
    href: 'https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap',
  },
]

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body>
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <Outlet />
    </AuthProvider>
  )
}

export function ErrorBoundary({ error }: Route.ErrorBoundaryProps) {
  const isNotFound = isRouteErrorResponse(error) && error.status === 404

  let label = 'エラー'
  let message = '問題が発生しました'
  let details =
    '予期しないエラーが発生しました。少し時間をおいて再度お試しください。'
  let stack: string | undefined

  if (isNotFound) {
    label = '404'
    message = 'ページが見つかりません'
    details = 'お探しのページは存在しないか、移動した可能性があります。'
  } else if (isRouteErrorResponse(error)) {
    label = String(error.status)
    details = error.statusText || details
  } else if (import.meta.env.DEV && error instanceof Error) {
    details = error.message
    stack = error.stack
  }

  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-6 bg-background px-4 py-16 text-center text-foreground">
      <div className="flex flex-col items-center gap-3">
        <span className="flex size-14 items-center justify-center rounded-full bg-muted text-muted-foreground">
          <CompassIcon className="size-7" aria-hidden />
        </span>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
          {label}
        </p>
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
          {message}
        </h1>
        <p className="max-w-md text-sm leading-relaxed text-muted-foreground">
          {details}
        </p>
      </div>

      <Button asChild>
        <Link to="/">ホームへ戻る</Link>
      </Button>

      {stack && (
        <pre className="mt-2 max-w-full overflow-x-auto rounded-lg bg-muted p-4 text-left text-xs text-muted-foreground">
          <code>{stack}</code>
        </pre>
      )}
    </main>
  )
}
