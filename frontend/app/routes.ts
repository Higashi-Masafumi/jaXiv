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
    route('terms', 'routes/legal/terms.tsx'),
    route('privacy', 'routes/legal/privacy.tsx'),
    route('commercial', 'routes/legal/commercial.tsx'),
  ]),
  route('login', 'routes/login.tsx'),
  route('auth/callback', 'routes/auth.callback.tsx'),
] satisfies RouteConfig
