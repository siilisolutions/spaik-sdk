import eslintReact from '@eslint-react/eslint-plugin';
import js from '@eslint/js';
import reactHooks from 'eslint-plugin-react-hooks';
import { defineConfig } from 'eslint/config';
import globals from 'globals';
import tseslint from 'typescript-eslint';

export default defineConfig(
    { ignores: ['dist'] },
    js.configs.recommended,
    tseslint.configs.recommended,
    eslintReact.configs['recommended-typescript'],
    reactHooks.configs.flat.recommended,
    {
        languageOptions: {
            globals: globals.browser,
        },
    },
    {
        // Both packages support React 18, which lacks <Context> providers and use()
        rules: {
            '@eslint-react/no-context-provider': 'off',
            '@eslint-react/no-use-context': 'off',
        },
    },
);
