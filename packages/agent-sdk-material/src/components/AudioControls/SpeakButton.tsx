import { IconButton, Tooltip, CircularProgress } from '@mui/material';
import { useTextToSpeech } from '@siilisolutions/ai-sdk-react';
import { VolumeUpIcon, VolumeOffIcon } from '../../utils/icons';

interface SpeakButtonProps {
    text: string;
    baseUrl: string;
    /** TTS model. Defaults to 'tts-1' (fast). Use 'tts-1-hd' for higher quality but slower. */
    model?: string;
    voice?: string;
    size?: 'small' | 'medium';
}

/**
 * Button to play text-to-speech for a message.
 * Shows a speaker icon that plays the text when clicked.
 */
export function SpeakButton({ 
    text, 
    baseUrl, 
    model = 'tts-1',  // Fast model by default
    voice = 'alloy',
    size = 'small' 
}: SpeakButtonProps) {
    const { speak, stop, isPlaying, isLoading } = useTextToSpeech({
        baseUrl,
        model,
        voice,
    });

    const handleClick = () => {
        if (isPlaying || isLoading) {
            stop();
        } else {
            speak(text);
        }
    };

    const getTooltip = () => {
        if (isLoading) return 'Cancel';
        if (isPlaying) return 'Stop';
        return 'Listen';
    };

    return (
        <Tooltip title={getTooltip()}>
            <IconButton 
                onClick={handleClick} 
                size={size}
                sx={{
                    color: (isPlaying || isLoading) ? 'primary.main' : 'action.active',
                    '&:hover': {
                        bgcolor: 'action.hover',
                    },
                }}
            >
                {isLoading ? (
                    <CircularProgress size={size === 'small' ? 16 : 20} />
                ) : isPlaying ? (
                    <VolumeOffIcon fontSize={size} />
                ) : (
                    <VolumeUpIcon fontSize={size} />
                )}
            </IconButton>
        </Tooltip>
    );
}
