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
                    width: '44px',
                    height: '44px',
                    borderRadius: '8px',
                    border: 'none',
                    backgroundColor: disabled ? '#f3f4f6' : '#f8f9fa',
                    color: disabled ? '#9ca3af' : '#6b7280',
                    fontSize: '18px',
                    cursor: disabled ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'all 0.15s ease',
                    flexShrink: 0,
                }}
                onMouseEnter={(e) => {
                    if (!disabled) {
                        e.currentTarget.style.backgroundColor = '#e9ecef';
                        e.currentTarget.style.color = '#495057';
                    }
                }}
                onMouseLeave={(e) => {
                    if (!disabled) {
                        e.currentTarget.style.backgroundColor = '#f8f9fa';
                        e.currentTarget.style.color = '#6b7280';
                    }
                }}
                title="Attach files (images, PDFs)"
            >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
                </svg>
            </button>
        </>
    );
}
