import { Box, Typography, IconButton, Tooltip } from '@mui/material';
import { DeleteOutlineIcon, RefreshIcon, MenuIcon } from '../../utils/icons';

interface Props {
    title?: string;
    onDelete?: () => void;
    onRefresh?: () => void;
    onMenuClick?: () => void;
    showMenuButton?: boolean;
}

export function ChatHeader({ title, onDelete, onRefresh, onMenuClick, showMenuButton }: Props) {
    return (
        <Box
            sx={{
                px: 2,
                py: 2,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderBottom: 1,
                borderColor: 'divider',
                bgcolor: 'background.paper',
            }}
        >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 0 }}>
                {showMenuButton && (
                    <IconButton size="small" onClick={onMenuClick} edge="start">
                        <MenuIcon />
                    </IconButton>
                )}
                <Typography variant="h6" fontWeight={600} noWrap sx={{ minWidth: 0 }}>
                    {title || 'Chat'}
                </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 0.5, flexShrink: 0 }}>
                {onRefresh && (
                    <Tooltip title="Refresh">
                        <IconButton size="small" onClick={onRefresh}>
                            <RefreshIcon fontSize="small" />
                        </IconButton>
                    </Tooltip>
                )}
                {onDelete && (
                    <Tooltip title="Delete thread">
                        <IconButton size="small" onClick={onDelete} color="error">
                            <DeleteOutlineIcon fontSize="small" />
                        </IconButton>
                    </Tooltip>
                )}
            </Box>
        </Box>
    );
}
