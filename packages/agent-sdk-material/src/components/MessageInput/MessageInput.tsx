import { useState, useMemo, useCallback } from 'react';
import { Box, TextField, IconButton, Paper, alpha, useTheme } from '@mui/material';
import {
    useThreadActions,
    useFileUploadStore,
    createFilesApiClient,
    PendingUpload,
} from '@siilisolutions/ai-sdk-react';
import { AttachButton } from './AttachButton';
import { PendingAttachments } from './PendingAttachments';
import { PushToTalkButton } from '../AudioControls/PushToTalkButton';
import { SendIcon, StopIcon } from '../../utils/icons';

interface Props {
    threadId: string;
    filesBaseUrl?: string;
    isGenerating?: boolean;
    onCancelGeneration?: () => void;
    enableSTT?: boolean;
}

export function MessageInput({ threadId, filesBaseUrl, isGenerating, onCancelGeneration, enableSTT = false }: Props) {
    const theme = useTheme();
    const [inputMessage, setInputMessage] = useState('');
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
        if ((!inputMessage.trim() && completedUploads.length === 0) || isGenerating || hasInProgress) {
            return;
        }

        const messageContent = inputMessage.trim();
        const attachments = completedUploads.map((u) => ({
            file_id: u.fileId!,
            mime_type: u.mimeType!,
            filename: u.file.name,
        }));

        // Clear input immediately
        setInputMessage('');
        clearCompleted();

        try {
            await sendMessage(threadId, {
                content: messageContent,
                attachments: attachments.length > 0 ? attachments : undefined,
            });
        } catch (error) {
            console.error('Failed to send message:', error);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    // Handler for voice input (push-to-talk)
    const handleSendVoice = useCallback(async (text: string) => {
        if (!text.trim() || isGenerating) return;
        
        try {
            await sendMessage(threadId, { content: text.trim() });
        } catch (error) {
            console.error('Failed to send voice message:', error);
        }
    }, [threadId, isGenerating, sendMessage]);

    const canSend =
        (inputMessage.trim() || completedUploads.length > 0) && !isGenerating && !hasInProgress;

    return (
        <Box sx={{ p: 2, bgcolor: 'background.default' }}>
            <Box sx={{ maxWidth: '900px', mx: 'auto', width: '100%' }}>
                <PendingAttachments uploads={allUploads} onRemove={removeUpload} />
                <Paper
                    elevation={0}
                    sx={{
                        display: 'flex',
                        alignItems: 'flex-end',
                        gap: 1.5,
                        p: 1.5,
                        pl: 2,
                        borderRadius: 5,
                        border: '1px solid',
                        borderColor: theme.palette.mode === 'dark' ? alpha(theme.palette.common.white, 0.15) : alpha(theme.palette.common.black, 0.1),
                        bgcolor: theme.palette.mode === 'dark' ? alpha(theme.palette.grey[900], 0.6) : '#fff',
                        boxShadow: theme.shadows[4],
                        transition: 'all 0.2s ease',
                        '&:focus-within': {
                            borderColor: 'primary.main',
                            boxShadow: `0 4px 12px ${alpha(theme.palette.primary.main, 0.2)}`,
                            transform: 'translateY(-1px)',
                        }
                    }}
                >
                    <AttachButton onFilesSelected={handleFilesSelected} disabled={isGenerating} />
                    {enableSTT && filesBaseUrl && (
                        <PushToTalkButton
                            baseUrl={filesBaseUrl}
                            onSend={handleSendVoice}
                            disabled={isGenerating}
                        />
                    )}
                    <TextField
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Type your message..."
                        disabled={isGenerating}
                        multiline
                        maxRows={5}
                        fullWidth
                        variant="standard"
                        InputProps={{
                            disableUnderline: true,
                            style: { fontSize: '0.95rem', lineHeight: 1.5 }
                        }}
                        sx={{
                            mb: 0.5,
                        }}
                    />
                    {isGenerating ? (
                        <IconButton
                            onClick={onCancelGeneration}
                            sx={{
                                width: 40,
                                height: 40,
                                color: 'common.white',
                                bgcolor: 'error.main',
                                '&:hover': {
                                    bgcolor: 'error.dark',
                                },
                                transition: 'all 0.2s',
                            }}
                        >
                            <StopIcon sx={{ fontSize: 20 }} />
                        </IconButton>
                    ) : (
                        <IconButton
                            onClick={handleSendMessage}
                            disabled={!canSend}
                            sx={{
                                width: 40,
                                height: 40,
                                color: canSend ? 'common.white' : 'action.disabled',
                                bgcolor: canSend ? 'primary.main' : alpha(theme.palette.action.disabledBackground, 0.1),
                                '&:hover': {
                                    bgcolor: canSend ? 'primary.dark' : alpha(theme.palette.action.disabledBackground, 0.1),
                                },
                                transition: 'all 0.2s',
                            }}
                        >
                            <SendIcon sx={{ fontSize: 20, ml: 0.5 }} />
                        </IconButton>
                    )}
                </Paper>
            </Box>
        </Box>
    );
}
