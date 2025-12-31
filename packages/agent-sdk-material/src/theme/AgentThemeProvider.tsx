import { createContext, useState, useMemo, useEffect, ReactNode } from 'react';
import { ThemeProvider, CssBaseline, Theme } from '@mui/material';
import { lightTheme, darkTheme } from './defaultTheme';

export type ThemeMode = 'light' | 'dark' | 'system';

export interface AgentThemeContextValue {
    mode: ThemeMode;
    setMode: (mode: ThemeMode) => void;
    toggleMode: () => void;
    isDark: boolean;
}

export const AgentThemeContext = createContext<AgentThemeContextValue | undefined>(undefined);

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
    const [systemPrefersDark, setSystemPrefersDark] = useState(false);

    useEffect(() => {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        setSystemPrefersDark(mediaQuery.matches);

        const handler = (e: MediaQueryListEvent) => setSystemPrefersDark(e.matches);
        mediaQuery.addEventListener('change', handler);
        return () => mediaQuery.removeEventListener('change', handler);
    }, []);

    const isDark = mode === 'dark' || (mode === 'system' && systemPrefersDark);

    const theme = useMemo(() => {
        if (isDark) {
            return customDarkTheme || darkTheme;
        }
        return customLightTheme || lightTheme;
    }, [isDark, customLightTheme, customDarkTheme]);

    const toggleMode = () => {
        setMode((prev) => {
            if (prev === 'light') return 'dark';
            if (prev === 'dark') return 'light';
            return isDark ? 'light' : 'dark';
        });
    };

    const contextValue = useMemo(
        () => ({ mode, setMode, toggleMode, isDark }),
        [mode, isDark]
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

