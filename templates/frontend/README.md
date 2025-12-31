# Frontend Template

React frontend template for Siili AI SDK.

## Setup

```bash
bun install
```

## Run

```bash
bun run dev
```

Open `http://localhost:5173`

Requires a backend at `http://localhost:8000`.

## Structure

```
src/
├── App.tsx                    # Provider setup
├── components/
│   ├── ThreadList/            # Thread sidebar
│   ├── ThreadView/            # Chat area with input
│   ├── MessageRenderer/       # Message display
│   └── MessageBlockRenderer/  # Block rendering (text, tools, etc.)
└── utils/
```

## Customization

### API URL

Edit `App.tsx`:

```tsx
const client = new AgentSdkClient({
  baseUrl: 'https://your-api.com',
  headers: {
    'Authorization': 'Bearer token',
  },
});
```

### Styling

Components use inline styles. Customize in component files or add your CSS framework.

### Message Blocks

Customize block rendering in `MessageBlockRenderer/`:

```tsx
function BlockContent({ block }: { block: MessageBlock }) {
  switch (block.type) {
    case 'plain':
      return <p>{block.content}</p>;
    case 'reasoning':
      return <details><summary>Thinking...</summary>{block.content}</details>;
    case 'tool_use':
      return <ToolCallDisplay block={block} />;
    case 'error':
      return <div className="error">{block.content}</div>;
  }
}
```

## Development

```bash
bun run dev      # Dev server
bun run build    # Production build
bun run preview  # Preview build
```
