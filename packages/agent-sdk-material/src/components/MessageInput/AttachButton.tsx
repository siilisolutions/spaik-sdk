import { useRef } from 'react';
import { IconButton, Tooltip } from '@mui/material';
import { AttachFileIcon } from '../../utils/icons';

interface Props {
    onFilesSelected: (files: File[]) => void;
    disabled?: boolean;
    accept?: string;
}

export function AttachButton({ onFilesSelected, disabled, accept = 'image/*,.pdf' }: Props) {
    const inputRef = useRef<HTMLInputElement>(null);

    const handleClick = () => {
        inputRef.current?.click();
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(e.target.files || []);
        if (files.length > 0) {
            onFilesSelected(files);
        }
        if (inputRef.current) {
            inputRef.current.value = '';
        }
    };

    return (
        <>
            <input
                ref={inputRef}
                type="file"
                multiple
                accept={accept}
                onChange={handleChange}
                style={{ display: 'none' }}
            />
            <Tooltip title="Attach files">
                <span>
                    <IconButton
                        onClick={handleClick}
                        disabled={disabled}
                        color="default"
                        sx={{
                            bgcolor: 'action.hover',
                            '&:hover': {
                                bgcolor: 'action.selected',
                            },
                        }}
                    >
                        <AttachFileIcon />
                    </IconButton>
                </span>
            </Tooltip>
        </>
    );
}
