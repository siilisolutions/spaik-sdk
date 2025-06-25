import asyncio
import threading
import time
from typing import Optional


class LangChainLoopManager:
    """Manages a persistent event loop for langchain operations"""

    def __init__(self):
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create the persistent event loop for langchain operations"""
        with self._lock:
            if self._loop is None or self._loop.is_closed():
                self._loop = None

                def run_loop():
                    self._loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(self._loop)
                    self._loop.run_forever()

                self._loop_thread = threading.Thread(target=run_loop, daemon=True)
                self._loop_thread.start()

                # Wait for loop to be created
                while self._loop is None:
                    time.sleep(0.01)

            return self._loop

    async def run_in_loop(self, coro):
        """Run a coroutine in the langchain loop and return the result"""
        loop = self.get_loop()

        try:
            current_loop = asyncio.get_running_loop()
            if current_loop != loop:
                # We're in a different loop context, run in langchain loop
                future = asyncio.run_coroutine_threadsafe(coro, loop)
                return future.result()
            else:
                # We're already in the langchain loop, run directly
                return await coro
        except RuntimeError:
            # No running loop, run in langchain loop
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            return future.result()

    async def stream_in_loop(self, async_generator):
        """Stream results from an async generator running in the langchain loop"""
        loop = self.get_loop()

        try:
            current_loop = asyncio.get_running_loop()
            if current_loop != loop:
                # We're in a different loop context, collect all results first
                future = asyncio.run_coroutine_threadsafe(self._collect_from_async_generator(async_generator), loop)
                results = future.result()
                for result in results:
                    yield result
            else:
                # We're already in the langchain loop, stream directly
                async for result in async_generator:
                    yield result
        except RuntimeError:
            # No running loop, collect all results first
            future = asyncio.run_coroutine_threadsafe(self._collect_from_async_generator(async_generator), loop)
            results = future.result()
            for result in results:
                yield result

    async def _collect_from_async_generator(self, async_generator):
        """Collect all items from an async generator"""
        results = []
        async for item in async_generator:
            results.append(item)
        return results


# Global instance
_loop_manager = LangChainLoopManager()


def get_langchain_loop_manager() -> LangChainLoopManager:
    """Get the global langchain loop manager instance"""
    return _loop_manager
