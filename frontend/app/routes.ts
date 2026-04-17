import {
  type RouteConfig,
  index,
  layout,
  route,
} from '@react-router/dev/routes'

export default [
  layout('layouts/app-layout.tsx', [
    index('routes/arxiv.tsx'),
    route('pdf', 'routes/pdf.tsx'),
    route('blog', 'routes/blog.tsx'),
    route('blog/:paperId', 'routes/blog.$paperId.tsx'),
    route('my-blogs', 'routes/my-blogs.tsx'),
  ]),
  route('login', 'routes/login.tsx'),
  route('auth/callback', 'routes/auth.callback.tsx'),
  route('api/blog/:paperId/chat', 'routes/api.blog.$paperId.chat.ts'),
] satisfies RouteConfig
