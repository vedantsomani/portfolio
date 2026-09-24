import js from '@eslint/js';
import astro from 'eslint-plugin-astro';
import globals from 'globals';
import tseslint from 'typescript-eslint';

export default [
  { ignores: ['dist/', '.astro/', '.vercel/', 'node_modules/'] },
  js.configs.recommended,
  ...tseslint.configs.strict,
  ...astro.configs.recommended,
  {
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
        // Build-time constants from astro.config.mjs (vite.define).
        __HAS_RESUME__: 'readonly',
        __HAS_TELEMETRY__: 'readonly',
        __MODELS__: 'readonly',
      },
    },
  },
];
