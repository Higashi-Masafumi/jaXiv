import js from '@eslint/js'
import globals from 'globals'
import tseslint from 'typescript-eslint'
import pluginReact from 'eslint-plugin-react'
import eslintConfigPrettier from 'eslint-config-prettier'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  {
    files: ['**/*.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    plugins: { js },
    extends: ['js/recommended'],
    languageOptions: { globals: globals.browser },
    settings: {
      react: {
        version: 'detect',
      },
    },
  },
  tseslint.configs.recommended,
  pluginReact.configs.flat.recommended,
  pluginReact.configs.flat['jsx-runtime'],
  eslintConfigPrettier,
  globalIgnores(['.react-router/types']),
  globalIgnores(['.storybook']),
  globalIgnores(['build']),
  globalIgnores(['node_modules']),
  globalIgnores(['dist']),
  globalIgnores(['.env']),
  globalIgnores(['.env.local']),
  globalIgnores(['.env.development.local']),
  globalIgnores(['.env.test.local']),
  globalIgnores(['.env.production.local']),
])
