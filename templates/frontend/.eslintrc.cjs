module.exports = {
    env: {
        browser: true,
        es2021: true,
        node: true
    },
    extends: [
        'eslint:recommended'
    ],
    parserOptions: {
        ecmaFeatures: {
            jsx: true
        },
        ecmaVersion: 'latest',
        sourceType: 'module'
    },
    rules: {
        'no-unused-vars': ['error', { argsIgnorePattern: '^_' }]
    },
    overrides: [
        {
            files: ['*.ts', '*.tsx'],
            rules: {
                // Disable JS rules for TS files since tsc handles them
                'no-unused-vars': 'off',
                'no-undef': 'off'
            }
        }
    ]
}; 