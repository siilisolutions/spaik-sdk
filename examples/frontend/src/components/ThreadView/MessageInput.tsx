import { useState, useMemo } from 'react';
import { useThreadActions, useFileUploadStore, type PendingUpload } from 'spaik-sdk-react';
import { createFilesApiClient } from 'spaik-sdk-react';
import { FileUploadButton } from '../FileUpload/FileUploadButton';
import { PendingUploads } from '../FileUpload/PendingUploads';

interface Props {
    threadId: string;
}

export function MessageInput({ threadId }: Props) {
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
        () => createFilesApiClient({ baseUrl: 'http://localhost:8000' }),
        []
    );

    const allUploads = Object.values(uploads);
    const completedUploads = allUploads.filter((u): u is PendingUpload => u.status === 'completed');
    const pendingOrUploading = allUploads.filter((u) => u.status === 'pending' || u.status === 'uploading');
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
        if ((!inputMessage.trim() && completedUploads.length === 0) || isSending || hasInProgress) return;

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

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const canSend = (inputMessage.trim() || completedUploads.length > 0) && !isSending && !hasInProgress;

    return (
        <div style={{
            padding: '16px 24px',
            borderTop: '1px solid #e1e5e9',
            backgroundColor: 'white'
        }}>
            <PendingUploads uploads={allUploads} onRemove={removeUpload} />
            <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
                <FileUploadButton 
                    onFilesSelected={handleFilesSelected} 
                    disabled={isSending}
                />
                <textarea
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Type your message here..."
                    disabled={isSending}
                    rows={1}
                    style={{
                        flex: 1,
                        height: '44px',
                        padding: '12px',
                        borderRadius: '8px',
                        border: '1px solid #d1d5db',
                        resize: 'none',
                        fontSize: '14px',
                        fontFamily: 'inherit',
                        outline: 'none',
                        transition: 'border-color 0.2s',
                        backgroundColor: isSending ? '#f9f9f9' : 'white',
                        overflow: 'hidden',
                        lineHeight: '20px',
                    }}
                    onFocus={(e) => e.target.style.borderColor = '#007bff'}
                    onBlur={(e) => e.target.style.borderColor = '#d1d5db'}
                />
                <button
                    onClick={handleSendMessage}
                    disabled={!canSend}
                    style={{
                        padding: '12px 20px',
                        borderRadius: '8px',
                        border: 'none',
                        backgroundColor: canSend ? '#007bff' : '#6c757d',
                        color: 'white',
                        fontSize: '14px',
                        fontWeight: '500',
                        cursor: canSend ? 'pointer' : 'not-allowed',
                        transition: 'background-color 0.2s',
                        minWidth: '80px'
                    }}
                >
                    {isSending ? 'Sending...' : hasInProgress ? 'Uploading...' : 'Send'}
                </button>
            </div>
        </div>
    );
}
