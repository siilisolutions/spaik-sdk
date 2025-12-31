import { Box, Typography, Avatar } from '@mui/material';
import { formatTimestamp, formatFullTimestamp } from '../../utils/formatTime';
import { SmartToyIcon, PersonIcon } from '../../utils/icons';

interface Props {
    authorName: string;
    isAi: boolean;
    timestamp: number;
    align?: 'left' | 'right';
}

export function MessageHeader({ authorName, isAi, timestamp, align = 'left' }: Props) {
    return (
        <Box
            sx={{
                display: 'flex',
                alignItems: 'center',
                flexDirection: align === 'right' ? 'row-reverse' : 'row',
                gap: 1.5,
                mb: 1,
                opacity: 0.9,
            }}
        >
            <Avatar
                sx={{
                    width: 24,
                    height: 24,
                    bgcolor: isAi ? 'primary.main' : 'secondary.main',
                }}
            >
                {isAi ? <SmartToyIcon sx={{ fontSize: 16 }} /> : <PersonIcon sx={{ fontSize: 16 }} />}
            </Avatar>
            
            <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1, flexDirection: align === 'right' ? 'row-reverse' : 'row' }}>
                <Typography
                    variant="subtitle2"
                    color="text.primary"
                    sx={{ fontWeight: 600 }}
                >
                    {authorName}
                </Typography>
                <Typography
                    variant="caption"
                    color="text.secondary"
                    title={formatFullTimestamp(timestamp)}
                >
                    {formatTimestamp(timestamp)}
                </Typography>
            </Box>
        </Box>
    );
}
