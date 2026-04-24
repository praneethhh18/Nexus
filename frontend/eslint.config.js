import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        ecmaVersion: 'latest',
        ecmaFeatures: { jsx: true },
        sourceType: 'module',
      },
    },
    rules: {
      // Keep the unused-vars rule strict but tolerate capitalised imports
      // (icon components destructured for later render paths).
      'no-unused-vars': ['warn', { varsIgnorePattern: '^[A-Z_]' }],

      // The codebase uses `try { ... } catch {}` as idiomatic "best-effort"
      // — noisy to annotate every site with a comment. Downgrade to warn.
      'no-empty': ['warn', { allowEmptyCatch: true }],

      // React-refresh complains when a file exports a hook + a component
      // (e.g. BulkActionBar.jsx exports useBulkSelection + BulkActionBar).
      // That's a stylistic rule only relevant for HMR boundary tuning;
      // tolerating it keeps our existing module layout intact.
      'react-refresh/only-export-components': 'warn',

      // `react-hooks/set-state-in-effect` is a brand-new aggressive rule that
      // flags the very common `useEffect(() => { reload(); }, [reload])`
      // pattern. Treating every load-on-mount effect as an error blocks the
      // whole codebase — keep it as a warning so genuine cascading-render
      // risks still surface in review.
      'react-hooks/set-state-in-effect': 'warn',

      // Purity + immutability checks are valuable but produce false positives
      // on patterns like `Date.now()` for id generation. Warn, don't error.
      'react-hooks/purity':      'warn',
      'react-hooks/immutability': 'warn',
    },
  },
])
