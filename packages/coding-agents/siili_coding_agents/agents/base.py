import asyncio
import gc
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator, Optional

from siili_ai_sdk import MessageBlock


class AgentConnectionError(Exception):
    """Raised when agent fails to connect or authenticate."""
    pass


@dataclass
class CommonOptions:
    """Common options shared by all coding agents"""
    model: Optional[str] = None
    working_directory: Optional[str] = None
    yolo: bool = False  # Auto-approve all actions without prompts
    verify_on_init: bool = True  # Verify connection on agent construction
    verify_timeout: float = 30.0  # Timeout for verification


class BaseCodingAgent(ABC):
    """Base class for all coding agents.
    
    All coding agents must implement:
    - run(prompt): Blocking execution
    - stream_blocks(prompt): Async streaming of MessageBlocks
    - get_setup_instructions(): Instructions for setting up the agent
    """
    
    def __init__(self, options: CommonOptions):
        self.common_options = options
        self._initialized = False
    
    def _post_init(self) -> None:
        """Called by subclasses after their __init__ completes.
        
        Runs verification if verify_on_init is True.
        """
        if self._initialized:
            return
        self._initialized = True
        
        if self.common_options.verify_on_init:
            self.verify_sync(self.common_options.verify_timeout)
    
    @property
    def model(self) -> Optional[str]:
        return self.common_options.model
    
    @property
    def working_directory(self) -> Optional[str]:
        return self.common_options.working_directory
    
    @property
    def yolo(self) -> bool:
        return self.common_options.yolo
    
    @abstractmethod
    def run(self, prompt: str) -> str:
        """Run the agent with the given prompt in blocking mode.
        
        Returns:
            The final result/response from the agent.
        """
        pass
    
    @abstractmethod
    def stream_blocks(self, prompt: str) -> AsyncGenerator[MessageBlock, None]:
        """Stream response blocks from the agent.
        
        Yields MessageBlock objects as the agent processes the prompt.
        """
        ...
    
    @abstractmethod
    def get_setup_instructions(self) -> str:
        """Return instructions for setting up this agent.
        
        Used when connection verification fails.
        """
        ...
    
    async def verify(self, timeout_seconds: float = 30.0) -> bool:
        """Verify the agent is properly configured and can respond.
        
        Sends a simple "say hi" prompt and waits for a response.
        
        Args:
            timeout_seconds: How long to wait before timing out.
            
        Returns:
            True if verification succeeded.
            
        Raises:
            AgentConnectionError: If verification fails or times out.
        """
        try:
            received_response = False
            
            async def _check():
                nonlocal received_response
                async for block in self.stream_blocks("say hi"):
                    if block.content:
                        received_response = True
                        return  # Got a response, we're good
            
            await asyncio.wait_for(_check(), timeout=timeout_seconds)
            
            if not received_response:
                raise AgentConnectionError(
                    f"Agent did not respond.\n\n{self.get_setup_instructions()}"
                )
            
            # Force cleanup of subprocess transports before loop closes
            gc.collect()
            return True
            
        except asyncio.TimeoutError:
            raise AgentConnectionError(
                f"Agent timed out after {timeout_seconds}s. "
                f"This usually means authentication is required.\n\n"
                f"{self.get_setup_instructions()}"
            )
        except Exception as e:
            raise AgentConnectionError(
                f"Agent verification failed: {e}\n\n{self.get_setup_instructions()}"
            )
    
    def verify_sync(self, timeout_seconds: float = 30.0) -> bool:
        """Synchronous version of verify()."""
        return asyncio.run(self.verify(timeout_seconds))
