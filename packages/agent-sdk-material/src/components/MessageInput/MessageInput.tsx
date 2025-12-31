import { useState, useMemo } from 'react';
import { Box, TextField, IconButton, Paper, CircularProgress, alpha, useTheme } from '@mui/material';
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
    onMessageSent?: () => void;
}

export function MessageInput({ threadId, filesBaseUrl, onMessageSent }: Props) {
    const theme = useTheme();
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

        const messageContent = inputMessage.trim();
        const attachments = completedUploads.map((u) => ({
            file_id: u.fileId!,
            mime_type: u.mimeType!,
            filename: u.file.name,
        }));

        // Clear input and show typing indicator immediately
        setInputMessage('');
        clearCompleted();
        setIsSending(true);
        onMessageSent?.();

        try {
            await sendMessage(threadId, {
                content: messageContent,
                attachments: attachments.length > 0 ? attachments : undefined,
            });
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
        <Box sx={{ p: 2, bgcolor: 'background.default' }}>
            <Box sx={{ maxWidth: '900px', mx: 'auto', width: '100%' }}>
                <PendingAttachments uploads={allUploads} onRemove={removeUpload} />
                <Paper
                    elevation={0}
                    sx={{
                        display: 'flex',
                        alignItems: 'flex-end',
                        gap: 1,
                        p: 1.5,
                        borderRadius: 4,
                        border: '1px solid',
                        borderColor: theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                        bgcolor: theme.palette.mode === 'dark' ? alpha(theme.palette.background.paper, 0.6) : 'background.paper',
                        backdropFilter: 'blur(10px)',
                        transition: 'border-color 0.2s, box-shadow 0.2s',
                        '&:focus-within': {
                            borderColor: 'primary.main',
                            boxShadow: `0 0 0 2px ${alpha(theme.palette.primary.main, 0.2)}`,
                        }
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
                        maxRows={5}
                        fullWidth
                        variant="standard"
                        InputProps={{
                            disableUnderline: true,
                        }}
                        sx={{
                            mb: 0.5, // Align with buttons
                        }}
                    />
                    <IconButton
                        onClick={handleSendMessage}
                        disabled={!canSend}
                        sx={{
                            color: canSend ? 'primary.main' : 'action.disabled',
                            bgcolor: canSend ? alpha(theme.palette.primary.main, 0.1) : 'transparent',
                            '&:hover': {
                                bgcolor: canSend ? alpha(theme.palette.primary.main, 0.2) : 'transparent',
                            },
                            transition: 'all 0.2s',
                        }}
                    >
                        {isSending ? (
                            <CircularProgress size={24} color="inherit" />
                        ) : (
                            <SendIcon />
                        )}
                    </IconButton>
                </Paper>
            </Box>
        </Box>
    );
}
