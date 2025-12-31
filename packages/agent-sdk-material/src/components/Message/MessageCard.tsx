import { Paper, Box, alpha, useTheme } from '@mui/material';
import { Message } from '@siilisolutions/ai-sdk-react';
import { MessageHeader } from './MessageHeader';
import { MessageContent } from './MessageContent';
import { AttachmentGallery } from './AttachmentGallery';

interface Props {
    message: Message;
    filesBaseUrl?: string;
}

export function MessageCard({ message, filesBaseUrl }: Props) {
    const theme = useTheme();
    const isAi = message.ai;

    return (
        <Box
            sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: isAi ? 'flex-start' : 'flex-end',
                width: '100%',
                mb: 3, // Increased spacing
            }}
        >
            <Paper
                elevation={0}
                sx={{
                    p: 2.5,
                    maxWidth: isAi ? '100%' : '85%', // Limit user message width
                    borderRadius: 3, // 12px -> 24px equivalent roughly
                    borderTopLeftRadius: isAi ? 4 : 24, // Chat bubble effect
                    borderTopRightRadius: isAi ? 24 : 4,
                    bgcolor: isAi 
                        ? 'transparent' // AI messages blend in
                        : theme.palette.mode === 'dark' 
                            ? alpha(theme.palette.primary.main, 0.1) 
                            : alpha(theme.palette.primary.main, 0.05),
                    border: isAi ? 'none' : '1px solid',
                    borderColor: isAi 
                        ? 'transparent' 
                        : theme.palette.mode === 'dark'
                            ? alpha(theme.palette.primary.main, 0.2)
                            : alpha(theme.palette.primary.main, 0.1),
                    // For AI messages, we might want a background if it helps reading code blocks
                    ...(isAi && {
                        width: '100%',
                        pl: 0, // Align with edge
                    }),
                }}
            >
                <MessageHeader
                    authorName={message.author_name}
                    isAi={message.ai}
                    timestamp={message.timestamp}
                    align={isAi ? 'left' : 'right'}
                />
                
                <Box sx={{ mt: 1 }}>
                    <MessageContent blocks={message.blocks} />
                    {message.attachments && message.attachments.length > 0 && (
                        <Box sx={{ mt: 2 }}>
                            <AttachmentGallery
                                attachments={message.attachments}
                                filesBaseUrl={filesBaseUrl}
                            />
                        </Box>
                    )}
                </Box>
            </Paper>
        </Box>
    );
}
