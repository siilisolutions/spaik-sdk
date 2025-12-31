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
        <Box
            sx={{
                borderRadius: 2,
                overflow: 'hidden',
                my: 1,
                bgcolor: alpha(theme.palette.secondary.main, 0.05),
                borderLeft: '3px solid',
                borderColor: alpha(theme.palette.secondary.main, 0.3),
            }}
        >
            <Box
                onClick={() => setExpanded(!expanded)}
                sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1.5,
                    px: 1.5,
                    py: 1,
                    cursor: 'pointer',
                    userSelect: 'none',
                    '&:hover': {
                        bgcolor: alpha(theme.palette.secondary.main, 0.08),
                    },
                }}
            >
                <PsychologyIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
                <Typography variant="caption" color="text.secondary" fontWeight={600} sx={{ flex: 1, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Reasoning Process
                </Typography>
                <IconButton
                    size="small"
                    sx={{
                        p: 0.5,
                        transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                        transition: 'transform 0.2s',
                    }}
                >
                    <ExpandMoreIcon fontSize="small" />
                </IconButton>
            </Box>
            <Collapse in={expanded}>
                <Box sx={{ p: 2, pt: 0 }}>
                    <Typography
                        variant="body2"
                        sx={{
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-word',
                            color: 'text.secondary',
                            fontFamily: 'monospace',
                            fontSize: '0.85rem',
                        }}
                    >
                        {content}
                    </Typography>
                </Box>
            </Collapse>
        </Box>
    );
}
