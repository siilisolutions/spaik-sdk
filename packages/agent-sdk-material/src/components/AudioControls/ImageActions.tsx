import { useState, useCallback } from 'react';
import { IconButton, Tooltip, Box, alpha, useTheme } from '@mui/material';
import { ContentCopyIcon, CheckIcon, DownloadIcon } from '../../utils/icons';

interface ImageActionsProps {
    imageUrl: string;
    filename?: string;
}

/**
 * Action buttons for images: copy to clipboard and download.
 * Displays as a floating overlay on hover.
 */
export function ImageActions({ imageUrl, filename = 'image.png' }: ImageActionsProps) {
    const theme = useTheme();
    const [copied, setCopied] = useState(false);

    const handleCopyImage = useCallback(async () => {
        try {
            const response = await fetch(imageUrl);
            const blob = await response.blob();
            
            // Use ClipboardItem API for copying images
            await navigator.clipboard.write([
                new ClipboardItem({
                    [blob.type]: blob,
                }),
            ]);
            
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy image:', err);
            // Fallback: copy URL
            try {
                await navigator.clipboard.writeText(imageUrl);
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
            } catch {
                console.error('Failed to copy image URL');
            }
        }
    }, [imageUrl]);

    const handleDownload = useCallback(async () => {
        try {
            const response = await fetch(imageUrl);
            const blob = await response.blob();
            
            // Create download link
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        } catch (err) {
            console.error('Failed to download image:', err);
        }
    }, [imageUrl, filename]);

    return (
        <Box
            sx={{
                position: 'absolute',
                top: 8,
                right: 8,
                display: 'flex',
                gap: 0.5,
                opacity: 0,
                transition: 'opacity 0.2s',
                '.image-container:hover &': {
                    opacity: 1,
                },
            }}
        >
            <Tooltip title={copied ? 'Copied!' : 'Copy image'}>
                <IconButton
                    onClick={handleCopyImage}
                    size="small"
                    sx={{
                        bgcolor: alpha(theme.palette.background.paper, 0.9),
                        backdropFilter: 'blur(4px)',
                        color: copied ? 'success.main' : 'text.primary',
                        boxShadow: 1,
                        '&:hover': {
                            bgcolor: 'background.paper',
                        },
                    }}
                >
                    {copied ? <CheckIcon fontSize="small" /> : <ContentCopyIcon fontSize="small" />}
                </IconButton>
            </Tooltip>
            <Tooltip title="Download">
                <IconButton
                    onClick={handleDownload}
                    size="small"
                    sx={{
                        bgcolor: alpha(theme.palette.background.paper, 0.9),
                        backdropFilter: 'blur(4px)',
                        color: 'text.primary',
                        boxShadow: 1,
                        '&:hover': {
                            bgcolor: 'background.paper',
                        },
                    }}
                >
                    <DownloadIcon fontSize="small" />
                </IconButton>
            </Tooltip>
        </Box>
    );
}
