import type { Config } from '@react-router/dev/config'

import { listBlogsApiV1BlogGet } from './app/api/sdk.gen'
export default {
  // Config options...
  // Server-side render by default, to enable SPA mode set this to `false`
  ssr: true,
  /**
   * Prerender the blog pages for performance
   * @returns The blog pages to prerender
   */
  async prerender() {
    const { data: blogs, error } = await listBlogsApiV1BlogGet({
      baseUrl: process.env.API_BASE_URL,
    })
    if (error || !blogs) {
      return []
    }
    return blogs.map(blog => `/blog/${blog.paper_id}`)
  },
} satisfies Config
