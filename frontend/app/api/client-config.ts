import { supabase } from '~/lib/supabase'
import { client } from './client.gen'

client.setConfig({
  baseUrl: import.meta.env.VITE_API_BASE_URL,
  auth: async () => {
    const {
      data: { session },
    } = await supabase.auth.getSession()
    return session?.access_token
  },
})
