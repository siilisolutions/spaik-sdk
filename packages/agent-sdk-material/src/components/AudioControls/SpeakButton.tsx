import { IconButton, Tooltip, CircularProgress } from '@mui/material';
import { useTextToSpeech } from '@siilisolutions/ai-sdk-react';
import { VolumeUpIcon, VolumeOffIcon } from '../../utils/icons';

interface SpeakButtonProps {
    text: string;
    baseUrl: string;
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
    model,
    voice = 'alloy',
    size = 'small' 
}: SpeakButtonProps) {
    const { speak, stop, isPlaying, isLoading } = useTextToSpeech({
        baseUrl,
        model,
        voice,
    });

    const handleClick = () => {
        if (isPlaying) {
            stop();
        } else {
            speak(text);
        }
    };

    if (isLoading) {
        return (
            <IconButton size={size} disabled>
                <CircularProgress size={size === 'small' ? 16 : 20} />
            </IconButton>
        );
    }

    return (
        <Tooltip title={isPlaying ? 'Stop' : 'Listen'}>
            <IconButton 
                onClick={handleClick} 
                size={size}
                sx={{
                    color: isPlaying ? 'primary.main' : 'action.active',
                    '&:hover': {
                        bgcolor: 'action.hover',
                    },
                }}
            >
                {isPlaying ? (
                    <VolumeOffIcon fontSize={size} />
                ) : (
                    <VolumeUpIcon fontSize={size} />
                )}
            </IconButton>
        </Tooltip>
    );
}
