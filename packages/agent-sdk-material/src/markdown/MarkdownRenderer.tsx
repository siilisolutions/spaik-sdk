import { useMemo, ComponentType } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Typography, Link, Box, Paper, useTheme, alpha } from '@mui/material';
import { useMarkdownContext, CustomComponentProps } from './MarkdownContext';
import { StoredImage } from './StoredImage';

interface MarkdownRendererProps {
    content: string;
}

// Regex to match self-closing XML tags like <ComponentName prop="value" />
const CUSTOM_TAG_REGEX = /<([A-Z][a-zA-Z0-9]*)\s*([^>]*?)\/>/g;

// Parse attributes from a string like: id="123" alt="hello"
function parseAttributes(attrString: string): CustomComponentProps {
    const attrs: CustomComponentProps = {};
    const attrRegex = /(\w+)=["']([^"']*)["']/g;
    let match;
    while ((match = attrRegex.exec(attrString)) !== null) {
        attrs[match[1]] = match[2];
    }
    return attrs;
}

/**
 * Splits content into segments of plain text and custom component invocations.
 */
function parseContent(content: string): Array<{ type: 'text'; value: string } | { type: 'component'; name: string; props: CustomComponentProps }> {
    const segments: Array<{ type: 'text'; value: string } | { type: 'component'; name: string; props: CustomComponentProps }> = [];
    let lastIndex = 0;
    let match;

    while ((match = CUSTOM_TAG_REGEX.exec(content)) !== null) {
        // Add text before this match
        if (match.index > lastIndex) {
            segments.push({ type: 'text', value: content.slice(lastIndex, match.index) });
        }
        
        // Add the component
        segments.push({
            type: 'component',
            name: match[1],
            props: parseAttributes(match[2]),
        });
        
        lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < content.length) {
        segments.push({ type: 'text', value: content.slice(lastIndex) });
    }

    return segments;
}

/**
 * Renders markdown content with support for custom components.
 * 
 * Custom components are specified as self-closing XML tags:
 * <StoredImage id="abc123" />
 * <CustomCard userId="456" />
 */
export function MarkdownRenderer({ content }: MarkdownRendererProps) {
    const theme = useTheme();
    const { customComponents } = useMarkdownContext();

    // Combine built-in components with user-provided ones
    const allComponents = useMemo((): Record<string, ComponentType<CustomComponentProps>> => ({
        StoredImage,
        ...customComponents,
    }), [customComponents]);

    const segments = useMemo(() => parseContent(content), [content]);

    const renderedContent = useMemo(() => {
        return segments.map((segment, index) => {
            if (segment.type === 'component') {
                const Component = allComponents[segment.name];
                if (Component) {
                    const props = segment.props;
                    return (
                        <Box key={index} component="span" sx={{ display: 'contents' }}>
                            <Component {...props} />
                        </Box>
                    );
                }
                // Unknown component - render as text
                return (
                    <Paper 
                        key={index}
                        variant="outlined" 
                        sx={{ 
                            display: 'inline-block', 
                            px: 1, 
                            py: 0.5,
                            bgcolor: 'warning.main',
                            color: 'warning.contrastText',
                            fontSize: '0.85rem',
                        }}
                    >
                        Unknown component: {segment.name}
                    </Paper>
                );
            }

            // Render markdown text
            return (
                <ReactMarkdown
                    key={index}
                    remarkPlugins={[remarkGfm]}
                    components={{
                        p: ({ children }) => (
                            <Typography variant="body1" sx={{ mb: 1.5, lineHeight: 1.7, '&:last-child': { mb: 0 } }}>
                                {children}
                            </Typography>
                        ),
                        h1: ({ children }) => (
                            <Typography variant="h4" fontWeight={700} sx={{ mt: 3, mb: 1.5 }}>
                                {children}
                            </Typography>
                        ),
                        h2: ({ children }) => (
                            <Typography variant="h5" fontWeight={600} sx={{ mt: 2.5, mb: 1 }}>
                                {children}
                            </Typography>
                        ),
                        h3: ({ children }) => (
                            <Typography variant="h6" fontWeight={600} sx={{ mt: 2, mb: 1 }}>
                                {children}
                            </Typography>
                        ),
                        h4: ({ children }) => (
                            <Typography variant="subtitle1" fontWeight={600} sx={{ mt: 1.5, mb: 0.5 }}>
                                {children}
                            </Typography>
                        ),
                        a: ({ href, children }) => (
                            <Link href={href} target="_blank" rel="noopener noreferrer" underline="hover">
                                {children}
                            </Link>
                        ),
                        ul: ({ children }) => (
                            <Box component="ul" sx={{ pl: 3, mb: 1.5, '& li': { mb: 0.5 } }}>
                                {children}
                            </Box>
                        ),
                        ol: ({ children }) => (
                            <Box component="ol" sx={{ pl: 3, mb: 1.5, '& li': { mb: 0.5 } }}>
                                {children}
                            </Box>
                        ),
                        li: ({ children }) => (
                            <Typography component="li" variant="body1" sx={{ lineHeight: 1.6 }}>
                                {children}
                            </Typography>
                        ),
                        blockquote: ({ children }) => (
                            <Box
                                component="blockquote"
                                sx={{
                                    borderLeft: '4px solid',
                                    borderColor: 'primary.main',
                                    pl: 2,
                                    py: 0.5,
                                    my: 1.5,
                                    bgcolor: alpha(theme.palette.primary.main, 0.05),
                                    borderRadius: 1,
                                    '& p': { mb: 0 },
                                }}
                            >
                                {children}
                            </Box>
                        ),
                        code: ({ className, children, ...props }) => {
                            const isInline = !className;
                            if (isInline) {
                                return (
                                    <Box
                                        component="code"
                                        sx={{
                                            bgcolor: alpha(theme.palette.text.primary, 0.08),
                                            px: 0.75,
                                            py: 0.25,
                                            borderRadius: 0.5,
                                            fontFamily: 'monospace',
                                            fontSize: '0.9em',
                                        }}
                                    >
                                        {children}
                                    </Box>
                                );
                            }
                            return (
                                <Paper
                                    variant="outlined"
                                    sx={{
                                        p: 2,
                                        my: 1.5,
                                        overflow: 'auto',
                                        bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50',
                                        '& code': {
                                            fontFamily: 'monospace',
                                            fontSize: '0.9rem',
                                            lineHeight: 1.5,
                                        },
                                    }}
                                >
                                    <code className={className} {...props}>
                                        {children}
                                    </code>
                                </Paper>
                            );
                        },
                        pre: ({ children }) => <>{children}</>,
                        strong: ({ children }) => (
                            <Box component="strong" sx={{ fontWeight: 600 }}>
                                {children}
                            </Box>
                        ),
                        em: ({ children }) => (
                            <Box component="em" sx={{ fontStyle: 'italic' }}>
                                {children}
                            </Box>
                        ),
                        hr: () => (
                            <Box
                                component="hr"
                                sx={{
                                    border: 'none',
                                    borderTop: '1px solid',
                                    borderColor: 'divider',
                                    my: 2,
                                }}
                            />
                        ),
                        img: ({ src, alt }) => (
                            <Box
                                component="img"
                                src={src}
                                alt={alt}
                                sx={{
                                    maxWidth: '100%',
                                    height: 'auto',
                                    borderRadius: 2,
                                    my: 1,
                                }}
                            />
                        ),
                        table: ({ children }) => (
                            <Box sx={{ overflowX: 'auto', my: 1.5 }}>
                                <Box
                                    component="table"
                                    sx={{
                                        width: '100%',
                                        borderCollapse: 'collapse',
                                        '& th, & td': {
                                            border: '1px solid',
                                            borderColor: 'divider',
                                            px: 1.5,
                                            py: 1,
                                            textAlign: 'left',
                                        },
                                        '& th': {
                                            bgcolor: alpha(theme.palette.primary.main, 0.08),
                                            fontWeight: 600,
                                        },
                                    }}
                                >
                                    {children}
                                </Box>
                            </Box>
                        ),
                    }}
                >
                    {segment.value}
                </ReactMarkdown>
            );
        });
    }, [segments, allComponents, theme]);

    return <Box sx={{ '& > *:first-of-type': { mt: 0 }, wordBreak: 'break-word', overflowWrap: 'anywhere' }}>{renderedContent}</Box>;
}
