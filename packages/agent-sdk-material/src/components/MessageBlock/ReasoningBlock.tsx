import { useState } from 'react';
import { Box, Collapse, IconButton, Typography, alpha, useTheme } from '@mui/material';
import { PsychologyIcon, ExpandMoreIcon } from '../../utils/icons';

interface Props {
    content: string;
}

export function ReasoningBlock({ content }: Props) {
    const theme = useTheme();
    const [expanded, setExpanded] = useState(false);

    if (!content) return null;

    return (
        <Box sx={{ my: 1.5 }}>
            <Box
                onClick={() => setExpanded(!expanded)}
                sx={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 1,
                    cursor: 'pointer',
                    borderRadius: 1,
                    px: 1,
                    py: 0.5,
                    color: 'text.secondary',
                    transition: 'all 0.2s',
                    '&:hover': {
                        color: 'text.primary',
                        bgcolor: alpha(theme.palette.text.primary, 0.05),
                    },
                }}
            >
                <PsychologyIcon sx={{ fontSize: 16 }} />
                <Typography variant="caption" fontWeight={600} sx={{ letterSpacing: '0.02em' }}>
                    {expanded ? 'Hide Reasoning' : 'View Reasoning'}
                </Typography>
                <ExpandMoreIcon 
                    sx={{ 
                        fontSize: 16,
                        transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                        transition: 'transform 0.2s'
                    }} 
                />
            </Box>
            
            <Collapse in={expanded}>
                <Box 
                    sx={{ 
                        mt: 1, 
                        pl: 2, 
                        borderLeft: '2px solid',
                        borderColor: 'divider',
                    }}
                >
                    <Typography
                        variant="body2"
                        sx={{
                            whiteSpace: 'pre-wrap',
                            color: 'text.secondary',
                            fontSize: '0.9rem',
                            fontFamily: theme.typography.fontFamily,
                            lineHeight: 1.6,
                        }}
                    >
                        {content}
                    </Typography>
                </Box>
            </Collapse>
        </Box>
    );
}
