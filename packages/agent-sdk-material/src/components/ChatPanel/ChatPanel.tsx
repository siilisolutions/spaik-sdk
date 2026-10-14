import { ReactNode } from 'react';
import { Box, Typography, IconButton } from '@mui/material';
import { Message, messageText, useThread, useThreadSelection, useThreadActions } from 'spaik-sdk-react';
import { ChatHeader } from './ChatHeader.js';
import { MessageList } from './MessageList.js';
import { MessageInput } from '../MessageInput/MessageInput.js';
import { MenuIcon } from '../../utils/icons.js';

interface Props {
    filesBaseUrl?: string;
    renderMessage?: (message: Message, messages: Message[]) => ReactNode;
    renderState?: (state: unknown) => ReactNode;
    onMenuClick?: () => void;
    showMenuButton?: boolean;
    enableTTS?: boolean;
    enableSTT?: boolean;
    enableCopy?: boolean;
    /** Language code for STT (e.g., 'en', 'fi'). Defaults to 'en'. */
    sttLanguage?: string;
}

export function ChatPanel({ filesBaseUrl, renderMessage, renderState, onMenuClick, showMenuButton, enableTTS = false, enableSTT = false, enableCopy = true, sttLanguage = 'en' }: Props) {
    const { selectedThreadId } = useThreadSelection();
    const { thread, state, error, loading, isGenerating } = useThread(selectedThreadId || '');
    const { cancelGeneration } = useThreadActions();
    const handleCancelGeneration = () => {
        if (selectedThreadId) {
            console.log('Cancelling generation for thread:', selectedThreadId);
            cancelGeneration(selectedThreadId);
        }
    };

    if (!selectedThreadId) {
        return (
            <Box
                sx={{
                    flex: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    bgcolor: 'background.default',
                }}
            >
                {showMenuButton && (
                    <Box sx={{ p: 1 }}>
                        <IconButton onClick={onMenuClick} edge="start">
                            <MenuIcon />
                        </IconButton>
                    </Box>
                )}
                <Box
                    sx={{
                        flex: 1,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                    }}
                >
                    <Typography color="text.secondary" variant="h6">
                        Select or create a thread to start chatting
                    </Typography>
                </Box>
            </Box>
        );
    }

    const firstMessage = thread?.messages?.[0];
    const title = firstMessage ? messageText(firstMessage).slice(0, 40) || 'Chat' : 'Chat';

    return (
        <Box
            sx={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                height: '100%',
                bgcolor: 'background.default',
            }}
        >
            <ChatHeader 
                title={title} 
                onMenuClick={onMenuClick}
                showMenuButton={showMenuButton}
            />
            <MessageList
                messages={thread?.messages}
                messageMetadata={thread?.message_metadata}
                renderMessage={renderMessage}
                isLoading={loading}
                filesBaseUrl={filesBaseUrl}
                showTypingIndicator={isGenerating}
                enableTTS={enableTTS}
                enableCopy={enableCopy}
            />
            {error && <Typography role="alert" color="error">{error}</Typography>}
            {renderState ? renderState(state) : Object.keys(state ?? {}).length > 0 ? <Box component="details"><summary>State</summary><pre>{JSON.stringify(state, null, 2)}</pre></Box> : null}
            <MessageInput 
                threadId={selectedThreadId} 
                filesBaseUrl={filesBaseUrl}
                isGenerating={isGenerating}
                onCancelGeneration={handleCancelGeneration}
                enableSTT={enableSTT}
                sttLanguage={sttLanguage}
            />
        </Box>
    );
}
