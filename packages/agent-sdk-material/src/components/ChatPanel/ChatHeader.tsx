import { Box, Typography, IconButton, Tooltip } from '@mui/material';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import RefreshIcon from '@mui/icons-material/Refresh';

interface Props {
    title?: string;
    onDelete?: () => void;
    onRefresh?: () => void;
}

export function ChatHeader({ title, onDelete, onRefresh }: Props) {
    return (
        <Box
            sx={{
                px: 3,
                py: 2,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderBottom: 1,
                borderColor: 'divider',
                bgcolor: 'background.paper',
            }}
        >
            <Typography variant="h6" fontWeight={600} noWrap>
                {title || 'Chat'}
            </Typography>
            <Box sx={{ display: 'flex', gap: 0.5 }}>
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

