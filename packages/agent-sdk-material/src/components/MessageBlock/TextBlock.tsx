import { Typography } from '@mui/material';

interface Props {
    content: string;
}

export function TextBlock({ content }: Props) {
    if (!content) return null;

    return (
        <Typography
            variant="body2"
            sx={{
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                lineHeight: 1.7,
            }}
        >
            {content}
        </Typography>
    );
}

