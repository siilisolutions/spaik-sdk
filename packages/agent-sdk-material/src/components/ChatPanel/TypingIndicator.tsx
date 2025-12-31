import { Box, keyframes } from '@mui/material';

const bounce = keyframes`
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-4px);
  }
`;

export function TypingIndicator() {
    return (
        <Box
            sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 0.5,
                p: 2,
                pl: 3,
            }}
        >
            {[0, 1, 2].map((i) => (
                <Box
                    key={i}
                    sx={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        bgcolor: 'primary.main',
                        animation: `${bounce} 1.4s ease-in-out infinite`,
                        animationDelay: `${i * 0.16}s`,
                    }}
                />
            ))}
        </Box>
    );
}

