import { createContext, useContext, ReactNode, ComponentType } from 'react';

/**
 * Props passed to custom markdown components.
 * The component receives all XML attributes as props.
 */
export interface CustomComponentProps {
    [key: string]: string | undefined;
}

/**
 * A map of component names to React components.
 * Used for rendering custom XML-like tags in markdown.
 * 
 * Example:
 * ```tsx
 * const customComponents = {
 *   StoredImage: ({ id }) => <img src={`/files/${id}`} />,
 *   UserCard: ({ userId }) => <UserCardComponent userId={userId} />,
 * };
 * ```
 */
export type CustomComponentRegistry = Record<string, ComponentType<CustomComponentProps>>;

interface MarkdownContextValue {
    customComponents: CustomComponentRegistry;
    filesBaseUrl?: string;
}

const MarkdownContext = createContext<MarkdownContextValue>({
    customComponents: {},
});

interface MarkdownProviderProps {
    children: ReactNode;
    /** Custom components to render XML-like tags in markdown */
    customComponents?: CustomComponentRegistry;
    /** Base URL for file service (used by built-in StoredImage) */
    filesBaseUrl?: string;
}

export function MarkdownProvider({ children, customComponents = {}, filesBaseUrl }: MarkdownProviderProps) {
    return (
        <MarkdownContext.Provider value={{ customComponents, filesBaseUrl }}>
            {children}
        </MarkdownContext.Provider>
    );
}

export function useMarkdownContext() {
    return useContext(MarkdownContext);
}
