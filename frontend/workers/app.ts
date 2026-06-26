import { createRequestHandler } from 'react-router'

declare module 'react-router' {
  export interface AppLoadContext {
    cloudflare: {
      env: Env
      ctx: ExecutionContext
    }
  }
}

const requestHandler = createRequestHandler(
  () => import('virtual:react-router/server-build'),
  import.meta.env.MODE,
)

export default {
  async fetch(request, env, ctx) {
    return requestHandler(request, {
      cloudflare: { env, ctx },
    })
  },
  // Render 無料プランは15分無アクセスでスピンダウンするため、
  // backend のヘルスエンドポイントを定期 ping して常時ウォーム状態に保つ。
  async scheduled(_controller, env, ctx) {
    ctx.waitUntil(
      (async () => {
        try {
          const res = await fetch(`${env.API_BASE_URL}/`, {
            method: 'GET',
            headers: { 'User-Agent': 'jaxiv-keepalive/1.0' },
          })
          console.log(`keepalive: backend responded ${res.status}`)
        } catch (err) {
          console.error('keepalive: backend ping failed', err)
        }
      })(),
    )
  },
} satisfies ExportedHandler<Env>
