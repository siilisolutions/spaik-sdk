import { Box, Chip, CircularProgress, alpha } from '@mui/material';
import { PendingUpload } from '@siilisolutions/ai-sdk-react';
import { CheckCircleIcon, ErrorIcon } from '../../utils/icons';

interface Props {
    uploads: PendingUpload[];
    onRemove: (id: string) => void;
}

export function PendingAttachments({ uploads, onRemove }: Props) {
    if (uploads.length === 0) return null;

    return (
        <Box
            sx={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: 1,
                px: 2,
                pt: 2,
            }}
        >
            {uploads.map((upload) => {
                const isUploading = upload.status === 'uploading' || upload.status === 'pending';
                const isCompleted = upload.status === 'completed';
                const isFailed = upload.status === 'error';

                return (
                    <Chip
                        key={upload.id}
                        label={upload.file.name}
                        onDelete={() => onRemove(upload.id)}
                        size="small"
                        color={isFailed ? 'error' : isCompleted ? 'success' : 'default'}
                        variant={isCompleted ? 'filled' : 'outlined'}
                        icon={
                            isUploading ? (
                                <CircularProgress size={14} sx={{ ml: 0.5 }} />
                            ) : isCompleted ? (
                                <CheckCircleIcon />
                            ) : isFailed ? (
                                <ErrorIcon />
                            ) : undefined
                        }
                        sx={{
                            maxWidth: 200,
                            '& .MuiChip-label': {
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                            },
                            ...(isCompleted && {
                                bgcolor: (theme) => alpha(theme.palette.success.main, 0.1),
                                borderColor: 'success.main',
                            }),
                        }}
                    />
                );
            })}
        </Box>
    );
}
