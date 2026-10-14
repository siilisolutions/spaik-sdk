import { Paper, Box, useTheme, Avatar, Typography, alpha } from '@mui/material';
import { Attachment, Message, messageText } from 'spaik-sdk-react';
import { MessageContent } from './MessageContent.js';
import { AttachmentGallery } from './AttachmentGallery.js';
import { SmartToyIcon, PersonIcon } from '../../utils/icons.js';
import { formatTimestamp } from '../../utils/formatTime.js';
import { SpeakButton } from '../AudioControls/SpeakButton.js';
import { CopyButton } from '../AudioControls/CopyButton.js';

interface Props {
    message: Message;
    messages?: Message[];
    metadata?: { timestamp?: number; author_name?: string; attachments?: Attachment[] };
    filesBaseUrl?: string;
    enableTTS?: boolean;
    enableCopy?: boolean;
}

export function MessageCard({ message, messages, metadata, filesBaseUrl, enableTTS = false, enableCopy = true }: Props) {
    const theme = useTheme();
    metadata = { ...(message.metadata?.spaik as Props['metadata']), ...metadata };
    const isAi = message.role !== 'user';
    const copyText = messageText(message);
    const ttsText = message.role === 'assistant' ? messageText(message) : '';
    const showActions = isAi && (copyText.length > 0 || ttsText.length > 0);

    return (
        <Box
            className="message-card"
            sx={{
                display: 'flex',
                flexDirection: isAi ? 'row' : 'row-reverse',
                gap: 2,
                mb: 4,
                px: 2,
                '&:hover .message-actions': {
                    opacity: 1,
                },
            }}
        >
            {/* Avatar Column */}
            <Box sx={{ flexShrink: 0, mt: 0.5 }}>
                <Avatar
                    sx={{
                        width: 32,
                        height: 32,
                        bgcolor: isAi ? 'primary.main' : 'secondary.main',
                        boxShadow: 2,
                    }}
                >
                    {isAi ? <SmartToyIcon sx={{ fontSize: 18 }} /> : <PersonIcon sx={{ fontSize: 18 }} />}
                </Avatar>
            </Box>

            {/* Message Column */}
            <Box
                sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: isAi ? 'flex-start' : 'flex-end',
                    maxWidth: '85%',
                    minWidth: 0, // Flexbox fix for text overflow
                }}
            >
                {/* Name & Time Row */}
                <Box 
                    sx={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: 1, 
                        mb: 0.5,
                        flexDirection: isAi ? 'row' : 'row-reverse',
                        opacity: 0.7,
                        px: 0.5
                    }}
                >
                    <Typography variant="caption" fontWeight={600} color="text.primary">
                        {metadata?.author_name ?? ('name' in message ? message.name ?? message.role : message.role)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                        {metadata?.timestamp ? formatTimestamp(metadata.timestamp) : null}
                    </Typography>
                </Box>

                {/* The Bubble / Content Area */}
                <Paper
                    elevation={0}
                    sx={{
                        p: isAi ? 0 : 2, // No padding for AI (text flow), Bubble for User
                        px: isAi ? 0 : 2.5,
                        borderRadius: isAi ? 0 : 3,
                        borderTopRightRadius: isAi ? 0 : 4,
                        bgcolor: isAi 
                            ? 'transparent' 
                            : theme.palette.mode === 'dark' 
                                ? 'primary.dark' 
                                : 'primary.main',
                        color: isAi ? 'text.primary' : 'primary.contrastText',
                        backgroundImage: 'none',
                        // Styles for user message text to ensure contrast
                        '& .MuiTypography-root': {
                            color: isAi ? 'text.primary' : 'inherit',
                        }
                    }}
                >
                    <MessageContent message={message} messages={messages} />
                    
                    {metadata?.attachments && metadata?.attachments.length > 0 && (
                        <Box sx={{ mt: 1.5 }}>
                            <AttachmentGallery
                                attachments={metadata?.attachments}
                                filesBaseUrl={filesBaseUrl}
                            />
                        </Box>
                    )}
                </Paper>

                {/* Action buttons for AI messages */}
                {showActions && (
                    <Box 
                        className="message-actions"
                        sx={{ 
                            display: 'flex', 
                            gap: 0.5, 
                            mt: 0.5,
                            opacity: 0,
                            transition: 'opacity 0.2s',
                            bgcolor: alpha(theme.palette.background.paper, 0.8),
                            borderRadius: 1,
                            p: 0.25,
                        }}
                    >
                        {enableCopy && copyText && (
                            <CopyButton text={copyText} size="small" />
                        )}
                        {enableTTS && ttsText && filesBaseUrl && (
                            <SpeakButton 
                                text={ttsText} 
                                baseUrl={filesBaseUrl}
                                size="small"
                            />
                        )}
                    </Box>
                )}
            </Box>
        </Box>
    );
}
