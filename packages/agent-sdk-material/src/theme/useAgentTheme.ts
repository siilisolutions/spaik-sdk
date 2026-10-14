import { useContext } from 'react';
import { AgentThemeContext, AgentThemeContextValue } from './AgentThemeProvider.js';

export function useAgentTheme(): AgentThemeContextValue {
    const context = useContext(AgentThemeContext);
    if (!context) {
        throw new Error('useAgentTheme must be used within AgentThemeProvider');
    }
    return context;
}

