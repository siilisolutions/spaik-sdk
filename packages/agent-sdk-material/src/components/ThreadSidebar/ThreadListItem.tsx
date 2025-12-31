import { ListItemButton, ListItemText, Typography, Box, alpha, useTheme } from '@mui/material';
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
    const theme = useTheme();

    return (
        <ListItemButton
            selected={isSelected}
            onClick={onClick}
            sx={{
                borderRadius: 2,
                mb: 0.5,
                mx: 1, // Add some margin from edge
                border: '1px solid transparent',
                '&.Mui-selected': {
                    bgcolor: alpha(theme.palette.primary.main, 0.1),
                    color: 'primary.main',
                    borderColor: alpha(theme.palette.primary.main, 0.2),
                    '&:hover': {
                        bgcolor: alpha(theme.palette.primary.main, 0.15),
                    },
                    '& .MuiTypography-root': {
                        color: 'primary.main',
                    },
                    '& .MuiSvgIcon-root': {
                        color: 'primary.main',
                    },
                    '& .MuiTypography-caption': {
                        color: alpha(theme.palette.primary.main, 0.8),
                    }
                },
            }}
        >
            <ListItemText
                primary={
                    <Typography
                        variant="body2"
                        fontWeight={isSelected ? 600 : 500}
                        noWrap
                        sx={{ mb: 0.5 }}
                    >
                        {title || 'New Thread'}
                    </Typography>
                }
                secondary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        <Typography variant="caption" className="MuiTypography-caption" color="text.secondary">
                            {formatTimestamp(lastActivity)}
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <ChatBubbleOutlineIcon sx={{ fontSize: 12, opacity: 0.7 }} />
                            <Typography variant="caption" className="MuiTypography-caption" color="text.secondary">
                                {messageCount}
                            </Typography>
                        </Box>
                    </Box>
                }
                secondaryTypographyProps={{ component: 'div' }}
            />
        </ListItemButton>
    );
}
