import { type RouteConfig, index, route } from '@react-router/dev/routes'

export default [
  index('routes/home.tsx'),
  route('blog/:paperId', 'routes/blog.$paperId.tsx'),
] satisfies RouteConfig
