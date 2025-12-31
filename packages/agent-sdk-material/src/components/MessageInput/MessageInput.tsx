import { useState, useMemo } from 'react';
import { Box, TextField, IconButton, Paper, CircularProgress } from '@mui/material';
import {
    useThreadActions,
    useFileUploadStore,
    createFilesApiClient,
    PendingUpload,
} from '@siilisolutions/ai-sdk-react';
import { AttachButton } from './AttachButton';
import { PendingAttachments } from './PendingAttachments';
import { SendIcon } from '../../utils/icons';

interface Props {
    threadId: string;
    filesBaseUrl?: string;
}

export function MessageInput({ threadId, filesBaseUrl }: Props) {
    const [inputMessage, setInputMessage] = useState('');
    const [isSending, setIsSending] = useState(false);
    const { sendMessage } = useThreadActions();

    const {
        uploads,
        addUpload,
        updateProgress,
        completeUpload,
        failUpload,
        removeUpload,
        clearCompleted,
    } = useFileUploadStore();

    const filesClient = useMemo(
        () => createFilesApiClient({ baseUrl: filesBaseUrl || '' }),
        [filesBaseUrl]
    );

    const allUploads = Object.values(uploads);
    const completedUploads = allUploads.filter(
        (u): u is PendingUpload => u.status === 'completed' && !!u.fileId && !!u.mimeType
    );
    const pendingOrUploading = allUploads.filter(
        (u) => u.status === 'pending' || u.status === 'uploading'
    );
    const hasInProgress = pendingOrUploading.length > 0;

    const handleFilesSelected = async (files: File[]) => {
        for (const file of files) {
            const localId = addUpload(file);
            try {
                updateProgress(localId, 50);
                const result = await filesClient.uploadFile(file);
                completeUpload(localId, result.file_id, result.mime_type);
            } catch (error) {
                failUpload(localId, error instanceof Error ? error.message : 'Upload failed');
            }
        }
    };

    const handleSendMessage = async () => {
        if ((!inputMessage.trim() && completedUploads.length === 0) || isSending || hasInProgress) {
            return;
        }

        setIsSending(true);
        try {
            const attachments = completedUploads.map((u) => ({
                file_id: u.fileId!,
                mime_type: u.mimeType!,
                filename: u.file.name,
            }));

            await sendMessage(threadId, {
                content: inputMessage.trim(),
                attachments: attachments.length > 0 ? attachments : undefined,
            });
            setInputMessage('');
            clearCompleted();
        } catch (error) {
            console.error('Failed to send message:', error);
        } finally {
            setIsSending(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const canSend =
        (inputMessage.trim() || completedUploads.length > 0) && !isSending && !hasInProgress;

    return (
        <Paper
            elevation={0}
            sx={{
                borderTop: 1,
                borderColor: 'divider',
                bgcolor: 'background.paper',
            }}
        >
            <PendingAttachments uploads={allUploads} onRemove={removeUpload} />
            <Box
                sx={{
                    display: 'flex',
                    alignItems: 'flex-end',
                    gap: 1,
                    p: 2,
                }}
            >
                <AttachButton onFilesSelected={handleFilesSelected} disabled={isSending} />
                <TextField
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Type your message..."
                    disabled={isSending}
                    multiline
                    maxRows={4}
                    fullWidth
                    size="small"
                    sx={{
                        '& .MuiOutlinedInput-root': {
                            borderRadius: 3,
                        },
                    }}
                />
                <IconButton
                    onClick={handleSendMessage}
                    disabled={!canSend}
                    color="primary"
                    sx={{
                        bgcolor: canSend ? 'primary.main' : 'action.disabledBackground',
                        color: canSend ? 'primary.contrastText' : 'action.disabled',
                        '&:hover': {
                            bgcolor: 'primary.dark',
                        },
                        '&.Mui-disabled': {
                            bgcolor: 'action.disabledBackground',
                        },
                    }}
                >
                    {isSending ? (
                        <CircularProgress size={24} color="inherit" />
                    ) : (
                        <SendIcon />
                    )}
                </IconButton>
            </Box>
        </Paper>
    );
}
