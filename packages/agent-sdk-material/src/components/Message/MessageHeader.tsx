import { Box, Typography, Chip } from '@mui/material';
import { formatTimestamp, formatFullTimestamp } from '../../utils/formatTime';
import { SmartToyIcon, PersonIcon } from '../../utils/icons';

interface Props {
    authorName: string;
    isAi: boolean;
    timestamp: number;
}

export function MessageHeader({ authorName, isAi, timestamp }: Props) {
    return (
        <Box
            sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                mb: 1.5,
            }}
        >
            <Chip
                icon={isAi ? <SmartToyIcon /> : <PersonIcon />}
                label={authorName}
                size="small"
                color={isAi ? 'primary' : 'default'}
                variant={isAi ? 'filled' : 'outlined'}
                sx={{
                    fontWeight: 500,
                    '& .MuiChip-icon': {
                        fontSize: 16,
                    },
                }}
            />
            <Typography
                variant="caption"
                color="text.secondary"
                title={formatFullTimestamp(timestamp)}
            >
                {formatTimestamp(timestamp)}
            </Typography>
        </Box>
    );
}
