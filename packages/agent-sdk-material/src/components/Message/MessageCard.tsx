import { Paper } from '@mui/material';
import { Message } from '@siilisolutions/ai-sdk-react';
import { MessageHeader } from './MessageHeader';
import { MessageContent } from './MessageContent';
import { AttachmentGallery } from './AttachmentGallery';

interface Props {
    message: Message;
    filesBaseUrl?: string;
}

export function MessageCard({ message, filesBaseUrl }: Props) {
    return (
        <Paper
            elevation={0}
            sx={{
                p: 2.5,
                mb: 2,
                border: 1,
                borderColor: 'divider',
                bgcolor: message.ai ? 'background.paper' : 'grey.50',
                ...(message.ai && {
                    borderLeft: 3,
                    borderLeftColor: 'primary.main',
                }),
            }}
        >
            <MessageHeader
                authorName={message.author_name}
                isAi={message.ai}
                timestamp={message.timestamp}
            />
            <MessageContent blocks={message.blocks} />
            {message.attachments && message.attachments.length > 0 && (
                <AttachmentGallery
                    attachments={message.attachments}
                    filesBaseUrl={filesBaseUrl}
                />
            )}
        </Paper>
    );
}

