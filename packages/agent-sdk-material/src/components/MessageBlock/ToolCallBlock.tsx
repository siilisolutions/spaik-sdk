import { useState } from 'react';
import { Box, Collapse, IconButton, Typography, CircularProgress, alpha, Chip } from '@mui/material';
import BuildIcon from '@mui/icons-material/Build';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';

interface Props {
    toolName?: string;
    args?: Record<string, unknown>;
    response?: string;
    error?: string;
    streaming?: boolean;
}

export function ToolCallBlock({ toolName, args, response, error, streaming }: Props) {
    const [expanded, setExpanded] = useState(false);

    const isComplete = !streaming && (response || error);
    const hasError = !!error;

    return (
        <Box
            sx={{
                borderRadius: 2,
                bgcolor: (theme) => alpha(theme.palette.info.main, 0.08),
                border: 1,
                borderColor: (theme) =>
                    hasError
                        ? alpha(theme.palette.error.main, 0.3)
                        : alpha(theme.palette.info.main, 0.2),
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
                        bgcolor: (theme) => alpha(theme.palette.info.main, 0.04),
                    },
                }}
            >
                <BuildIcon fontSize="small" color="info" />
                <Chip
                    label={toolName || 'Tool Call'}
                    size="small"
                    variant="outlined"
                    color="info"
                    sx={{ fontFamily: 'monospace', fontWeight: 500 }}
                />
                <Box sx={{ flex: 1 }} />
                {streaming && <CircularProgress size={16} />}
                {isComplete && !hasError && (
                    <CheckCircleIcon fontSize="small" color="success" />
                )}
                {hasError && <ErrorIcon fontSize="small" color="error" />}
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
                <Box sx={{ px: 2, pb: 2 }}>
                    {args && Object.keys(args).length > 0 && (
                        <Box sx={{ mb: 1 }}>
                            <Typography variant="caption" color="text.secondary" fontWeight={500}>
                                Arguments:
                            </Typography>
                            <Box
                                component="pre"
                                sx={{
                                    mt: 0.5,
                                    p: 1.5,
                                    borderRadius: 1,
                                    bgcolor: 'background.default',
                                    fontSize: 12,
                                    fontFamily: 'monospace',
                                    overflow: 'auto',
                                    maxHeight: 200,
                                }}
                            >
                                {JSON.stringify(args, null, 2)}
                            </Box>
                        </Box>
                    )}
                    {response && (
                        <Box>
                            <Typography variant="caption" color="text.secondary" fontWeight={500}>
                                Response:
                            </Typography>
                            <Box
                                component="pre"
                                sx={{
                                    mt: 0.5,
                                    p: 1.5,
                                    borderRadius: 1,
                                    bgcolor: 'background.default',
                                    fontSize: 12,
                                    fontFamily: 'monospace',
                                    overflow: 'auto',
                                    maxHeight: 200,
                                    whiteSpace: 'pre-wrap',
                                    wordBreak: 'break-word',
                                }}
                            >
                                {response}
                            </Box>
                        </Box>
                    )}
                    {error && (
                        <Box>
                            <Typography variant="caption" color="error" fontWeight={500}>
                                Error:
                            </Typography>
                            <Typography
                                variant="body2"
                                color="error"
                                sx={{ mt: 0.5, fontFamily: 'monospace' }}
                            >
                                {error}
                            </Typography>
                        </Box>
                    )}
                </Box>
            </Collapse>
        </Box>
    );
}

