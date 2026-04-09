import json
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from langchain_core.tools import BaseTool, StructuredTool, tool
from pydantic import BaseModel, Field, create_model

from spaik_sdk.thread.models import MessageBlock


class ToolProvider(ABC):
    """
    Abstract class for tool providers.
    """

    def __init__(self, persist_tool_block_history: bool = True) -> None:
        self.persist_tool_block_history = persist_tool_block_history

    @abstractmethod
    def get_tools(self) -> List[BaseTool]:
        """
        Returns a Langchain BaseTool implementation.

        Returns:
            BaseTool: A Langchain tool
        """
        pass

    def get_provider_id(self) -> str:
        return f"{self.__class__.__module__}.{self.__class__.__qualname__}"

    def render_tool_block_for_history(self, block: MessageBlock) -> str:
        if not getattr(self, "persist_tool_block_history", True):
            return self.render_tool_call_marker(block)
        return self.render_tool_call_details(block)

    @staticmethod
    def render_tool_call_marker(block: MessageBlock) -> str:
        tool_name = block.tool_name or "unknown"
        return f'<tool_call tool="{tool_name}"/>'

    @staticmethod
    def render_tool_call_details(block: MessageBlock) -> str:
        payload: Dict[str, Any] = {"tool": block.tool_name or "unknown"}

        if block.tool_call_id is not None:
            payload["tool_call_id"] = block.tool_call_id
        if block.tool_call_args is not None:
            payload["args"] = block.tool_call_args
        if block.tool_call_response is not None:
            payload["response"] = block.tool_call_response
        if block.tool_call_error is not None:
            payload["error"] = block.tool_call_error

        return f"<tool_call>{json.dumps(payload, sort_keys=True)}</tool_call>"

    @staticmethod
    def create_tool(
        func: Callable[..., Any], name: str, description: str, args_schema: Optional[type[BaseModel]] = None, **kwargs
    ) -> BaseTool:
        """
        Create a tool with customizable name and description.

        Args:
            func: The function to wrap as a tool
            name: The tool name
            description: The tool description (overrides docstring)
            args_schema: Optional Pydantic model for argument validation
            **kwargs: Additional arguments passed to StructuredTool.from_function

        Returns:
            BaseTool: A configured langchain tool

        Example:
            def my_func(text: str) -> str:
                return f"Processed: {text}"

            # Basic usage
            tool = create_tool(my_func, "process", "Process text input")

            # With custom schema
            class MyArgs(BaseModel):
                text: str = Field(description="Text to process")

            tool = create_tool(my_func, "process", "Process text", MyArgs)
        """
        return StructuredTool.from_function(func=func, name=name, description=description, args_schema=args_schema, **kwargs)

    @staticmethod
    def create_dynamic_tool(
        func: Callable[..., Any], name: str, description: str, args: Optional[Dict[str, Union[type, Tuple[type, str]]]] = None, **kwargs
    ) -> BaseTool:
        """
        Create a tool with dynamic argument schema.

        Args:
            func: The function to wrap as a tool
            name: The tool name
            description: The tool description
            args: Dict mapping arg names to types or (type, description) tuples
            **kwargs: Additional arguments passed to StructuredTool.from_function

        Returns:
            BaseTool: A configured langchain tool

        Example:
            def search(query: str, limit: int = 10) -> str:
                return f"Found results for {query}"

            tool = create_dynamic_tool(
                search,
                "search_tool",
                "Search for information",
                args={
                    "query": (str, "The search query"),
                    "limit": (int, "Max results (default: 10)")
                }
            )
        """
        args_schema = None
        if args:
            # Build field definitions for dynamic schema
            fields = {}
            for arg_name, arg_spec in args.items():
                if isinstance(arg_spec, tuple):
                    arg_type, arg_desc = arg_spec
                    fields[arg_name] = (arg_type, Field(description=arg_desc))
                else:
                    fields[arg_name] = (arg_spec, Field())

            # Create dynamic Pydantic model
            args_schema = create_model(f"{name}Args", **fields)

        return StructuredTool.from_function(func=func, name=name, description=description, args_schema=args_schema, **kwargs)

    @staticmethod
    def create_simple_tool(func: Callable[..., Any], name: str, description: str, **kwargs) -> BaseTool:
        """
        Create a simple tool without argument validation.

        Args:
            func: The function to wrap as a tool
            name: The tool name
            description: The tool description
            **kwargs: Additional arguments passed to StructuredTool.from_function

        Returns:
            BaseTool: A configured langchain tool

        Example:
            def get_time() -> str:
                import datetime
                return datetime.datetime.now().isoformat()

            tool = create_simple_tool(
                get_time,
                "current_time",
                "Get current timestamp"
            )
        """
        return StructuredTool.from_function(func=func, name=name, description=description, **kwargs)


# Re-export langchain tools for convenience
__all__ = ["ToolProvider", "BaseTool", "tool"]
