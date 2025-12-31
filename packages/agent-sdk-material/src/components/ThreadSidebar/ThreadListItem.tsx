import { ListItemButton, ListItemText, Typography, Box } from '@mui/material';
import { formatTimestamp } from '../../utils/formatTime';
import { ChatBubbleOutlineIcon } from '../../utils/icons';

interface Props {
    title: string;
    messageCount: number;
    lastActivity: number;
    isSelected: boolean;
    onClick: () => void;
}

export function ThreadListItem({ title, messageCount, lastActivity, isSelected, onClick }: Props) {
    return (
        <ListItemButton
            selected={isSelected}
            onClick={onClick}
            sx={{
                borderRadius: 2,
                mb: 0.5,
                '&.Mui-selected': {
                    bgcolor: 'primary.main',
                    color: 'primary.contrastText',
                    '&:hover': {
                        bgcolor: 'primary.dark',
                    },
                    '& .MuiTypography-root': {
                        color: 'inherit',
                    },
                    '& .MuiSvgIcon-root': {
                        color: 'inherit',
                    },
                },
            }}
        >
            <ListItemText
                primary={
                    <Typography
                        variant="body2"
                        fontWeight={500}
                        noWrap
                        sx={{ mb: 0.5 }}
                    >
                        {title || 'New Thread'}
                    </Typography>
                }
                secondary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <ChatBubbleOutlineIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
                            <Typography variant="caption" color="text.secondary">
                                {messageCount}
                            </Typography>
                        </Box>
                        <Typography variant="caption" color="text.secondary">
                            {formatTimestamp(lastActivity)}
                        </Typography>
                    </Box>
                }
                secondaryTypographyProps={{ component: 'div' }}
            />
        </ListItemButton>
    );
}
