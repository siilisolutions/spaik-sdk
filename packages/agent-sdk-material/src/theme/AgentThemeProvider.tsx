import { createContext, useState, useMemo, useCallback, useSyncExternalStore, ReactNode } from 'react';
import { ThemeProvider, CssBaseline, Theme } from '@mui/material';
import { lightTheme, darkTheme } from './defaultTheme.js';

export type ThemeMode = 'light' | 'dark' | 'system';

export interface AgentThemeContextValue {
    mode: ThemeMode;
    setMode: (mode: ThemeMode) => void;
    toggleMode: () => void;
    isDark: boolean;
}

export const AgentThemeContext = createContext<AgentThemeContextValue | undefined>(undefined);

const DARK_QUERY = '(prefers-color-scheme: dark)';

function subscribeToColorScheme(onChange: () => void) {
    const mediaQuery = window.matchMedia(DARK_QUERY);
    mediaQuery.addEventListener('change', onChange);
    return () => mediaQuery.removeEventListener('change', onChange);
}

interface Props {
    children: ReactNode;
    defaultMode?: ThemeMode;
    lightTheme?: Theme;
    darkTheme?: Theme;
}

export function AgentThemeProvider({
    children,
    defaultMode = 'system',
    lightTheme: customLightTheme,
    darkTheme: customDarkTheme,
}: Props) {
    const [mode, setMode] = useState<ThemeMode>(defaultMode);
    const systemPrefersDark = useSyncExternalStore(
        subscribeToColorScheme,
        () => window.matchMedia(DARK_QUERY).matches,
        () => false
    );

    const isDark = mode === 'dark' || (mode === 'system' && systemPrefersDark);

    const theme = useMemo(() => {
        if (isDark) {
            return customDarkTheme || darkTheme;
        }
        return customLightTheme || lightTheme;
    }, [isDark, customLightTheme, customDarkTheme]);

    const toggleMode = useCallback(() => {
        setMode((prev) => {
            if (prev === 'light') return 'dark';
            if (prev === 'dark') return 'light';
            return isDark ? 'light' : 'dark';
        });
    }, [isDark]);

    const contextValue = useMemo(
        () => ({ mode, setMode, toggleMode, isDark }),
        [mode, isDark, toggleMode]
    );

    return (
        <AgentThemeContext.Provider value={contextValue}>
            <ThemeProvider theme={theme}>
                <CssBaseline />
                {children}
            </ThemeProvider>
        </AgentThemeContext.Provider>
    );
}

