import { useCallback } from 'react';
import { IconButton, Tooltip, CircularProgress, Box, alpha, useTheme } from '@mui/material';
import { usePushToTalk } from 'spaik-sdk-react';
import { MicIcon, StopIcon } from '../../utils/icons';

interface VoiceInputButtonProps {
    baseUrl: string;
    language?: string;
    onSend: (text: string) => Promise<void>;
    disabled?: boolean;
}

/**
 * Voice input button - click to start recording, click again to stop and send.
 */
export function PushToTalkButton({ 
    baseUrl, 
    language,
    onSend,
    disabled = false,
}: VoiceInputButtonProps) {
    const theme = useTheme();

    const { 
        startRecording, 
        stopRecording, 
        isRecording, 
        isTranscribing,
        error,
    } = usePushToTalk({
        baseUrl,
        language,
        onSend,
    });

    const handleClick = useCallback(async () => {
        if (disabled || isTranscribing) return;
        
        if (isRecording) {
            await stopRecording();
        } else {
            await startRecording();
        }
    }, [disabled, isRecording, isTranscribing, startRecording, stopRecording]);

    const getTooltip = () => {
        if (error) return `Error: ${error}`;
        if (isTranscribing) return 'Transcribing...';
        if (isRecording) return 'Click to stop and send';
        return 'Click to start recording';
    };

    return (
        <Tooltip title={getTooltip()}>
            <Box sx={{ position: 'relative', display: 'inline-flex' }}>
                <IconButton
                    onClick={handleClick}
                    disabled={disabled || isTranscribing}
                    sx={{
                        width: 40,
                        height: 40,
                        color: isRecording 
                            ? 'common.white' 
                            : error 
                                ? 'error.main' 
                                : 'action.active',
                        bgcolor: isRecording 
                            ? 'error.main' 
                            : alpha(theme.palette.action.active, 0.04),
                        '&:hover': {
                            bgcolor: isRecording 
                                ? 'error.dark' 
                                : alpha(theme.palette.action.active, 0.08),
                        },
                        transition: 'all 0.2s',
                        // Pulse animation when recording
                        ...(isRecording && {
                            animation: 'pulse 1.5s infinite',
                            '@keyframes pulse': {
                                '0%': {
                                    boxShadow: `0 0 0 0 ${alpha(theme.palette.error.main, 0.7)}`,
                                },
                                '70%': {
                                    boxShadow: `0 0 0 10px ${alpha(theme.palette.error.main, 0)}`,
                                },
                                '100%': {
                                    boxShadow: `0 0 0 0 ${alpha(theme.palette.error.main, 0)}`,
                                },
                            },
                        }),
                    }}
                >
                    {isRecording ? (
                        <StopIcon sx={{ fontSize: 20 }} />
                    ) : (
                        <MicIcon sx={{ fontSize: 20 }} />
                    )}
                </IconButton>
                {isTranscribing && (
                    <CircularProgress
                        size={44}
                        sx={{
                            position: 'absolute',
                            top: -2,
                            left: -2,
                            color: 'primary.main',
                        }}
                    />
                )}
            </Box>
        </Tooltip>
    );
}
