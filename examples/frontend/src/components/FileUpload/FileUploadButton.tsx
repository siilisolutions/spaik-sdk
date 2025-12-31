import { useRef } from 'react';

interface Props {
    onFilesSelected: (files: File[]) => void;
    disabled?: boolean;
    accept?: string;
}

export function FileUploadButton({ onFilesSelected, disabled, accept }: Props) {
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
                accept={accept || 'image/*,.pdf'}
                onChange={handleChange}
                style={{ display: 'none' }}
            />
            <button
                type="button"
                onClick={handleClick}
                disabled={disabled}
                style={{
                    padding: '12px',
                    borderRadius: '8px',
                    border: '1px solid #d1d5db',
                    backgroundColor: disabled ? '#f3f4f6' : 'white',
                    color: disabled ? '#9ca3af' : '#374151',
                    fontSize: '14px',
                    cursor: disabled ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'background-color 0.2s, border-color 0.2s',
                }}
                title="Attach files"
            >
                📎
            </button>
        </>
    );
}

