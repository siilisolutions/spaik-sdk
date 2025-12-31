import { Box, Typography, alpha } from '@mui/material';
import { ErrorOutlineIcon } from '../../utils/icons';

interface Props {
    content: string;
}

export function ErrorBlock({ content }: Props) {
    if (!content) return null;

    return (
        <Box
            sx={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: 1,
                p: 2,
                borderRadius: 2,
                bgcolor: (theme) => alpha(theme.palette.error.main, 0.08),
                border: 1,
                borderColor: (theme) => alpha(theme.palette.error.main, 0.3),
            }}
        >
            <ErrorOutlineIcon color="error" fontSize="small" sx={{ mt: 0.25 }} />
            <Typography variant="body2" color="error.main" sx={{ whiteSpace: 'pre-wrap' }}>
                {content}
            </Typography>
        </Box>
    );
}
