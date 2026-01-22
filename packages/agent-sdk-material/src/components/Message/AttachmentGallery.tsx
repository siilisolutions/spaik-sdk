import { Box, Paper, Typography, Link } from '@mui/material';
import { Attachment } from '@spaik/react';
import { ImageIcon, PictureAsPdfIcon, AudioFileIcon, VideoFileIcon, InsertDriveFileIcon } from '../../utils/icons';

interface Props {
    attachments: Attachment[];
    filesBaseUrl?: string;
}

function getFileUrl(fileId: string, filesBaseUrl?: string): string {
    const base = filesBaseUrl || '';
    return `${base}/files/${fileId}`;
}

function getIcon(mimeType: string) {
    if (mimeType.startsWith('image/')) return <ImageIcon />;
    if (mimeType === 'application/pdf') return <PictureAsPdfIcon />;
    if (mimeType.startsWith('audio/')) return <AudioFileIcon />;
    if (mimeType.startsWith('video/')) return <VideoFileIcon />;
    return <InsertDriveFileIcon />;
}

export function AttachmentGallery({ attachments, filesBaseUrl }: Props) {
    if (!attachments.length) return null;

    const images = attachments.filter((a) => a.mime_type.startsWith('image/'));
    const others = attachments.filter((a) => !a.mime_type.startsWith('image/'));

    return (
        <Box sx={{ mt: 2 }}>
            {images.length > 0 && (
                <Box
                    sx={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: 1,
                        mb: others.length > 0 ? 2 : 0,
                    }}
                >
                    {images.map((attachment) => (
                        <Paper
                            key={attachment.file_id}
                            component="a"
                            href={getFileUrl(attachment.file_id, filesBaseUrl)}
                            target="_blank"
                            rel="noopener noreferrer"
                            elevation={0}
                            sx={{
                                overflow: 'hidden',
                                borderRadius: 2,
                                border: 1,
                                borderColor: 'divider',
                                textDecoration: 'none',
                                transition: 'transform 0.2s, box-shadow 0.2s',
                                '&:hover': {
                                    transform: 'scale(1.02)',
                                    boxShadow: 2,
                                },
                            }}
                        >
                            <Box
                                component="img"
                                src={getFileUrl(attachment.file_id, filesBaseUrl)}
                                alt={attachment.filename || 'Attachment'}
                                sx={{
                                    width: 120,
                                    height: 120,
                                    objectFit: 'cover',
                                    display: 'block',
                                }}
                            />
                        </Paper>
                    ))}
                </Box>
            )}

            {others.length > 0 && (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {others.map((attachment) => (
                        <Link
                            key={attachment.file_id}
                            href={getFileUrl(attachment.file_id, filesBaseUrl)}
                            target="_blank"
                            rel="noopener noreferrer"
                            underline="none"
                        >
                            <Paper
                                elevation={0}
                                sx={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 1,
                                    px: 2,
                                    py: 1,
                                    border: 1,
                                    borderColor: 'divider',
                                    borderRadius: 2,
                                    transition: 'background-color 0.2s',
                                    '&:hover': {
                                        bgcolor: 'action.hover',
                                    },
                                }}
                            >
                                {getIcon(attachment.mime_type)}
                                <Typography variant="body2" noWrap sx={{ maxWidth: 150 }}>
                                    {attachment.filename || 'File'}
                                </Typography>
                            </Paper>
                        </Link>
                    ))}
                </Box>
            )}
        </Box>
    );
}
