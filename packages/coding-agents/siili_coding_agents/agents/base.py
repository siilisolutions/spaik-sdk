from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional

from siili_ai_sdk import MessageBlock


@dataclass
class CommonOptions:
    """Common options shared by all coding agents"""
    model: Optional[str] = None
    working_directory: Optional[str] = None
    yolo: bool = False  # Auto-approve all actions without prompts


class BaseCodingAgent(ABC):
    """Base class for all coding agents.
    
    All coding agents must implement:
    - run(prompt): Blocking execution
    - stream_blocks(prompt): Async streaming of MessageBlocks
    """
    
    def __init__(self, options: CommonOptions):
        self.common_options = options
    
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
    def run(self, prompt: str) -> None:
        """Run the agent with the given prompt in blocking mode.
        
        Output is printed to stdout.
        """
        pass
    
    @abstractmethod
    def stream_blocks(self, prompt: str) -> AsyncGenerator[MessageBlock, None]:
        """Stream response blocks from the agent.
        
        Yields MessageBlock objects as the agent processes the prompt.
        """
        ...

