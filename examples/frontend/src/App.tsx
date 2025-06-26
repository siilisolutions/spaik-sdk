import { ThreadList } from './components/ThreadList/ThreadList';
import { ThreadView } from './components/ThreadView/ThreadView';
import { useThreadSelection } from '@siili-ai-sdk/hooks';
import { NoThreadSelected } from './components/ThreadView/EmptyStates';


export function App() {
    const { selectedThreadId } = useThreadSelection();
    return (
        <div style={{
            display: 'flex',
            height: '100vh',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
        }}>
            <ThreadList />

            {selectedThreadId ? (
                <ThreadView
                    threadId={selectedThreadId}
                />
            ) : (
                <NoThreadSelected />
            )}


        </div>
    );
}