import { Box, CircularProgress, Paper, Typography } from '@mui/material';
import { useState } from 'react';
import { useMarkdownContext, CustomComponentProps } from './MarkdownContext';
import { ImageActions } from '../components/AudioControls/ImageActions';

interface StoredImageProps extends CustomComponentProps {
    id?: string;
    alt?: string;
    width?: string;
    height?: string;
}

/**
 * Built-in component for rendering images stored in the file service.
 * Use in markdown as: <StoredImage id="file-id-here" />
 * Includes copy and download actions on hover.
 */
export function StoredImage({ id, alt, width, height }: StoredImageProps) {
    const { filesBaseUrl } = useMarkdownContext();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);

    if (!id) {
        return (
            <Paper 
                variant="outlined" 
                sx={{ 
                    p: 2, 
                    display: 'inline-block', 
                    color: 'error.main',
                    borderColor: 'error.main',
                }}
            >
                <Typography variant="body2">StoredImage: missing id prop</Typography>
            </Paper>
        );
    }

    const imageUrl = filesBaseUrl ? `${filesBaseUrl}/files/${id}` : `/files/${id}`;

    if (error) {
        return (
            <Paper 
                variant="outlined" 
                sx={{ 
                    p: 2, 
                    display: 'inline-block',
                    color: 'text.secondary',
                    borderColor: 'divider',
                }}
            >
                <Typography variant="body2" color="text.secondary">
                    Failed to load image
                </Typography>
                <Typography variant="caption" color="text.disabled" sx={{ display: 'block', mt: 0.5 }}>
                    URL: {imageUrl}
                </Typography>
            </Paper>
        );
    }

    return (
        <Box 
            className="image-container"
            sx={{ 
                display: 'inline-block', 
                position: 'relative',
                my: 1,
                maxWidth: '100%',
            }}
        >
            {loading && (
                <Box 
                    sx={{ 
                        position: 'absolute', 
                        inset: 0, 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'center',
                        bgcolor: 'action.hover',
                        borderRadius: 2,
                        minHeight: 100,
                        minWidth: 100,
                    }}
                >
                    <CircularProgress size={24} />
                </Box>
            )}
            <Box
                component="img"
                src={imageUrl}
                alt={alt || 'Generated image'}
                onLoad={() => setLoading(false)}
                onError={(e) => {
                    console.error('StoredImage load error:', { id, imageUrl, event: e });
                    setLoading(false);
                    setError(true);
                }}
                sx={{
                    display: loading ? 'none' : 'block',
                    maxWidth: '100%',
                    height: 'auto',
                    borderRadius: 2,
                    boxShadow: 2,
                    ...(width && { width: parseInt(width) || width }),
                    ...(height && { height: parseInt(height) || height }),
                }}
            />
            {!loading && !error && (
                <ImageActions 
                    imageUrl={imageUrl} 
                    filename={`image-${id}.png`}
                />
            )}
        </Box>
    );
}
