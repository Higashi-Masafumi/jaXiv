import {
  type RouteConfig,
  index,
  layout,
  route,
} from '@react-router/dev/routes'

export default [
  layout('layouts/app-layout.tsx', [
    index('routes/home.tsx'),
    route('archive', 'routes/archive.tsx'),
    route('blog/:paperId', 'routes/blog.$paperId.tsx'),
  ]),
] satisfies RouteConfig
