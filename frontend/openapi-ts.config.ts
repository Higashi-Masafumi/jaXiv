import { defineConfig } from '@hey-api/openapi-ts'

export default defineConfig({
  input: '../backend/openapi.json',
  output: {
    path: 'app/api',
    postProcess: ['prettier'],
  },
  plugins: ['@hey-api/typescript', '@hey-api/sdk', '@hey-api/client-fetch'],
})
