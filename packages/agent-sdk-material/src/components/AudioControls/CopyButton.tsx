import { useState, useCallback } from 'react';
import { IconButton, Tooltip } from '@mui/material';
import { ContentCopyIcon, CheckIcon } from '../../utils/icons';

interface CopyButtonProps {
    text: string;
    size?: 'small' | 'medium';
    tooltipPlacement?: 'top' | 'bottom' | 'left' | 'right';
}

/**
 * Button to copy text content to clipboard.
 * Shows a checkmark briefly after successful copy.
 */
export function CopyButton({ 
    text, 
    size = 'small',
    tooltipPlacement = 'top',
}: CopyButtonProps) {
    const [copied, setCopied] = useState(false);

    const handleCopy = useCallback(async () => {
        try {
            await navigator.clipboard.writeText(text);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    }, [text]);

    return (
        <Tooltip title={copied ? 'Copied!' : 'Copy'} placement={tooltipPlacement}>
            <IconButton 
                onClick={handleCopy} 
                size={size}
                sx={{
                    color: copied ? 'success.main' : 'action.active',
                    '&:hover': {
                        bgcolor: 'action.hover',
                    },
                }}
            >
                {copied ? (
                    <CheckIcon fontSize={size} />
                ) : (
                    <ContentCopyIcon fontSize={size} />
                )}
            </IconButton>
        </Tooltip>
    );
}
