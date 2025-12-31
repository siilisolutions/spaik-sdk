import { createTheme, ThemeOptions, alpha } from '@mui/material/styles';

const commonOptions: ThemeOptions = {
    typography: {
        fontFamily: '"Inter", "Segoe UI", "Roboto", "Helvetica", "Arial", sans-serif',
        h6: {
            fontWeight: 600,
            letterSpacing: '-0.025em',
        },
        subtitle1: {
            fontWeight: 600,
            letterSpacing: '-0.025em',
        },
        subtitle2: {
            fontWeight: 600,
        },
        body1: {
            lineHeight: 1.6,
        },
        body2: {
            fontSize: '0.875rem',
            lineHeight: 1.5,
        },
        button: {
            fontWeight: 500,
            textTransform: 'none',
        },
    },
    shape: {
        borderRadius: 16,
    },
    components: {
        MuiButton: {
            styleOverrides: {
                root: {
                    borderRadius: 10,
                    padding: '8px 16px',
                    boxShadow: 'none',
                    '&:hover': {
                        boxShadow: 'none',
                    },
                },
                contained: {
                    '&:hover': {
                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
                    },
                },
            },
        },
        MuiPaper: {
            styleOverrides: {
                root: {
                    backgroundImage: 'none',
                },
            },
        },
        MuiCard: {
            styleOverrides: {
                root: {
                    backgroundImage: 'none',
                    boxShadow: 'none',
                    border: '1px solid',
                },
            },
        },
        MuiChip: {
            styleOverrides: {
                root: {
                    fontWeight: 500,
                },
                sizeSmall: {
                    fontSize: '0.75rem',
                },
            },
        },
        MuiTextField: {
            styleOverrides: {
                root: {
                    '& .MuiOutlinedInput-root': {
                        borderRadius: 12,
                    },
                },
            },
        },
    },
};

// Modern Indigo/Slate theme
export const lightTheme = createTheme({
    ...commonOptions,
    palette: {
        mode: 'light',
        primary: {
            main: '#4f46e5', // Indigo 600
            light: '#6366f1',
            dark: '#4338ca',
            contrastText: '#ffffff',
        },
        secondary: {
            main: '#64748b', // Slate 500
            light: '#94a3b8',
            dark: '#475569',
            contrastText: '#ffffff',
        },
        background: {
            default: '#f8fafc', // Slate 50
            paper: '#ffffff',
        },
        text: {
            primary: '#0f172a', // Slate 900
            secondary: '#475569', // Slate 600
        },
        divider: '#e2e8f0', // Slate 200
        action: {
            hover: alpha('#000', 0.04),
            selected: alpha('#4f46e5', 0.08),
        },
        grey: {
            50: '#f8fafc',
            100: '#f1f5f9',
            200: '#e2e8f0',
            300: '#cbd5e1',
            400: '#94a3b8',
            500: '#64748b',
            600: '#475569',
            700: '#334155',
            800: '#1e293b',
            900: '#0f172a',
        },
    },
});

export const darkTheme = createTheme({
    ...commonOptions,
    palette: {
        mode: 'dark',
        primary: {
            main: '#6366f1', // Indigo 500
            light: '#818cf8',
            dark: '#4f46e5',
            contrastText: '#ffffff',
        },
        secondary: {
            main: '#94a3b8', // Slate 400
            light: '#cbd5e1',
            dark: '#64748b',
            contrastText: '#0f172a',
        },
        background: {
            default: '#09090b', // Zinc 950
            paper: '#18181b', // Zinc 900
        },
        text: {
            primary: '#f4f4f5', // Zinc 100
            secondary: '#a1a1aa', // Zinc 400
        },
        divider: '#27272a', // Zinc 800
        action: {
            hover: alpha('#fff', 0.04),
            selected: alpha('#6366f1', 0.12),
        },
        grey: {
            50: '#fafafa',
            100: '#f4f4f5',
            200: '#e4e4e7',
            300: '#d4d4d8',
            400: '#a1a1aa',
            500: '#71717a',
            600: '#52525b',
            700: '#3f3f46',
            800: '#27272a',
            900: '#18181b',
        },
    },
    components: {
        ...commonOptions.components,
        MuiCard: {
            styleOverrides: {
                root: {
                    borderColor: '#27272a',
                    backgroundImage: 'none',
                },
            },
        },
    },
});
