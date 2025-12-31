import { useState } from 'react';
import { Box, Collapse, IconButton, Typography, alpha } from '@mui/material';
import { PsychologyIcon, ExpandMoreIcon } from '../../utils/icons';

interface Props {
    content: string;
}

export function ReasoningBlock({ content }: Props) {
    const [expanded, setExpanded] = useState(false);

    if (!content) return null;

    return (
        <Box
            sx={{
                borderRadius: 2,
                bgcolor: (theme) => alpha(theme.palette.secondary.main, 0.08),
                border: 1,
                borderColor: (theme) => alpha(theme.palette.secondary.main, 0.2),
            }}
        >
            <Box
                onClick={() => setExpanded(!expanded)}
                sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    px: 2,
                    py: 1,
                    cursor: 'pointer',
                    '&:hover': {
                        bgcolor: (theme) => alpha(theme.palette.secondary.main, 0.04),
                    },
                }}
            >
                <PsychologyIcon fontSize="small" color="secondary" />
                <Typography variant="body2" color="secondary" fontWeight={500} sx={{ flex: 1 }}>
                    Reasoning
                </Typography>
                <IconButton
                    size="small"
                    sx={{
                        transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                        transition: 'transform 0.2s',
                    }}
                >
                    <ExpandMoreIcon fontSize="small" />
                </IconButton>
            </Box>
            <Collapse in={expanded}>
                <Typography
                    variant="body2"
                    sx={{
                        px: 2,
                        pb: 2,
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                        color: 'text.secondary',
                        fontStyle: 'italic',
                    }}
                >
                    {content}
                </Typography>
            </Collapse>
        </Box>
    );
}
