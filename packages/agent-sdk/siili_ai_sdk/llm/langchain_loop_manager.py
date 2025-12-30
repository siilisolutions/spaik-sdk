"""
LangChain Loop Manager - Event Loop Isolation for Models with Event Loop Issues

This module exists to work around a fundamental incompatibility between certain
model providers (Google/Gemini, Ollama) and the way asyncio.run() manages event loops.

THE PROBLEM:
============
Some model providers (Google's gRPC-based clients, Ollama's async HTTP client, etc.)
create internal connections and async state that get bound to the specific
event loop instance they're created in. When that event loop closes, these
internal connections become unusable and raise "Event loop is closed" errors.

This manifests in two scenarios:

1. STANDALONE SCRIPTS with multiple asyncio.run() calls:
   ```python
   asyncio.run(main())  # Creates event loop, Google client binds to it
   # Event loop closes here
   asyncio.run(main())  # Creates NEW event loop, but Google client still references old one
   # → RuntimeError: Event loop is closed
   ```

2. WEB SERVERS (FastAPI, etc.) with persistent event loops:
   ```python
   # Web server starts one event loop and keeps it running
   # All requests use the SAME loop, so Google client works fine
   ```

THE WORKAROUND:
===============
We detect the execution context and apply different strategies:

1. **Standalone Context** (detected by stack frame inspection):
   - Use a persistent background event loop in a separate thread
   - All affected model operations run in this persistent loop
   - The background loop never closes, so the clients stay happy

2. **Web Server Context** (detected by uvicorn/fastapi in call stack):
   - Use normal execution (no loop manager)
   - The web server's persistent loop handles everything naturally

WHY WEB SERVERS CAN'T USE THE LOOP MANAGER:
===========================================
Web servers MUST NOT use the external event loop approach because:

1. **Streaming breaks**: When operations run in a separate thread's event loop,
   you lose the ability to stream results back to the web server's event loop
   in real-time. The thread boundary kills the streaming semantics.

2. **Request context isolation**: Web frameworks expect all operations for a
   request to happen in the same event loop to maintain proper async context,
   request isolation, and cancellation semantics.

3. **Performance overhead**: Cross-thread async communication adds significant
   latency and complexity that's unnecessary when the web server already
   provides a persistent event loop.

The key insight: Web servers naturally solve these client issues by having
persistent event loops, so they don't need (and can't use) the workaround.

DETECTION STRATEGY:
===================
We use multiple heuristics to detect execution context:
- Thread names (uvicorn, fastapi, etc.)
- Call stack inspection (looking for web framework files)
- Event loop state (persistent vs transient)

This is admittedly hacky, but it's the only way to transparently handle
both contexts without requiring users to explicitly configure the behavior.

AFFECTED MODELS:
================
- All Google/Gemini models (provider_type == ProviderType.GOOGLE)
- All Ollama models (provider_type == ProviderType.OLLAMA)
- Other providers (Anthropic, OpenAI) are unaffected

EXAMPLES:
=========
```python
# This would fail with Gemini without the loop manager:
asyncio.run(agent.get_response("hello"))
asyncio.run(agent.get_response("world"))  # ← RuntimeError

# This works fine with web servers (no loop manager needed):
@app.post("/chat")
async def chat():
    return await agent.get_response("hello")  # Same persistent loop
```

ALTERNATIVES CONSIDERED:
========================
1. Process isolation - Too heavy, breaks streaming
2. Raw Google API - Bypasses LangChain ecosystem
3. Client recreation - Google's state is deeper than we can reach
4. Thread-per-call - Breaks async/await semantics
5. User configuration - Poor DX, easy to get wrong

WHY THIS IS NECESSARY:
======================
Some client designs assume a long-lived event loop (like in web servers).
The asyncio.run() pattern creates short-lived loops that violate this assumption.
Other providers (Anthropic, OpenAI) handle this gracefully by recreating connections
or using stateless clients.

This is a known limitation that's unlikely to be fixed in these clients
since it would require significant architectural changes on their end.
"""

import asyncio
import threading
import time
from typing import Optional

from siili_ai_sdk.models.llm_config import LLMConfig
from siili_ai_sdk.models.providers.provider_type import ProviderType
from siili_ai_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


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


def _is_in_web_server_context() -> bool:
    """Detect if we're running in a web server/FastAPI context vs standalone asyncio.run()."""
    try:
        # Check if we're in an event loop
        loop = asyncio.get_running_loop()

        # FastAPI/web servers typically run event loops indefinitely
        # Check for common web server indicators in the call stack
        import inspect
        import threading

        # Get current thread name - web servers often have descriptive thread names
        thread_name = threading.current_thread().name
        if any(name in thread_name.lower() for name in ["uvicorn", "fastapi", "starlette", "asgi", "wsgi"]):
            return True

        # Check the call stack for web framework indicators
        frame = inspect.currentframe()
        try:
            while frame:
                frame_info = inspect.getframeinfo(frame)
                filename = frame_info.filename.lower()

                # Look for web framework files in the call stack
                if any(
                    indicator in filename
                    for indicator in ["uvicorn", "fastapi", "starlette", "asgi", "wsgi", "tornado", "aiohttp", "sanic", "quart"]
                ):
                    return True

                frame = frame.f_back
        finally:
            del frame

        # Check if the event loop has been running for a while (web servers)
        # vs just started (asyncio.run())
        if hasattr(loop, "_ready") and hasattr(loop._ready, "__len__") and len(loop._ready) > 0:  # type: ignore[arg-type]
            # This is a heuristic - web servers tend to have more pending tasks
            return True

        return False

    except RuntimeError:
        # No running event loop - definitely not in a web server
        return False
    except Exception as e:
        logger.debug(f"Error detecting web server context: {e}")
        return False


def _needs_loop_manager(llm_config: LLMConfig) -> bool:
    """Check if this model provider might have event loop issues with multiple asyncio.run() calls."""
    return llm_config.provider_type in (ProviderType.GOOGLE, ProviderType.OLLAMA)


def should_use_loop_manager(llm_config: LLMConfig) -> bool:
    """Determine if we should use the loop manager for models with event loop issues."""
    if not _needs_loop_manager(llm_config):
        return False

    # Only use loop manager if NOT in a web server context
    # Web servers have persistent event loops, so the issue doesn't occur
    return not _is_in_web_server_context()


# Global instance
_loop_manager = LangChainLoopManager()


def get_langchain_loop_manager() -> LangChainLoopManager:
    """Get the global langchain loop manager instance"""
    return _loop_manager
