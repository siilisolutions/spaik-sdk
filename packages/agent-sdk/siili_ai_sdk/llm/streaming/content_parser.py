from typing import Any, Dict, Optional, Tuple

from siili_ai_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


class ContentParser:
    """Handles parsing of chunk content to extract reasoning and regular content."""

    def parse_chunk_content(self, chunk) -> Tuple[Optional[str], Optional[str]]:
        """Parse chunk content and extract reasoning vs regular content."""
        reasoning_content = None
        regular_content = None

        # Check for reasoning in additional_kwargs (o3-mini responses API format)
        if hasattr(chunk, "additional_kwargs") and chunk.additional_kwargs:
            reasoning_data = chunk.additional_kwargs.get("reasoning")
            if reasoning_data:
                reasoning_content = self._extract_reasoning_from_data(reasoning_data)
                logger.debug(f"Reasoning data found: {reasoning_data}")

        # Check for reasoning summary in responses API format
        if hasattr(chunk, "summary") and chunk.summary:
            reasoning_content = self._extract_reasoning_from_summary(chunk.summary)

        # Parse content blocks
        if hasattr(chunk, "content"):
            reasoning_content, regular_content = self._parse_content_blocks(chunk.content, reasoning_content, regular_content)

        return reasoning_content, regular_content

    def parse_tool_calls(self, chunk) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, Any]]]:
        """Parse tool calls from chunk and return tool_call_id, tool_name, and tool_args."""
        tool_call_id = None
        tool_name = None
        tool_args = None

        # Check for tool calls in chunk
        if hasattr(chunk, "tool_calls") and chunk.tool_calls:
            # Handle list of tool calls (OpenAI format)
            for tool_call in chunk.tool_calls:
                if hasattr(tool_call, "id"):
                    tool_call_id = tool_call.id
                if hasattr(tool_call, "function"):
                    tool_name = tool_call.function.name
                    if hasattr(tool_call.function, "arguments"):
                        try:
                            import json

                            tool_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                        except json.JSONDecodeError:
                            tool_args = {"raw_arguments": tool_call.function.arguments}
                break  # Handle first tool call for now

        # Check for Anthropic tool use in content blocks
        if hasattr(chunk, "content") and isinstance(chunk.content, list):
            for content_block in chunk.content:
                if isinstance(content_block, dict):
                    if content_block.get("type") == "tool_use":
                        tool_call_id = content_block.get("id")
                        tool_name = content_block.get("name")
                        tool_args = content_block.get("input", {})
                        break
                elif hasattr(content_block, "type") and getattr(content_block, "type") == "tool_use":
                    tool_call_id = getattr(content_block, "id", None)
                    tool_name = getattr(content_block, "name", None)
                    tool_args = getattr(content_block, "input", {})
                    break

        return tool_call_id, tool_name, tool_args

    def parse_tool_response(self, chunk) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Parse tool response from chunk and return tool_call_id, response, and error."""
        tool_call_id = None
        response = None
        error = None

        # Check for tool response in content blocks (Anthropic format)
        if hasattr(chunk, "content") and isinstance(chunk.content, list):
            for content_block in chunk.content:
                if isinstance(content_block, dict):
                    if content_block.get("type") == "tool_result":
                        tool_call_id = content_block.get("tool_use_id")
                        if content_block.get("is_error"):
                            error = content_block.get("content", [{}])[0].get("text", "Tool execution error")
                        else:
                            response = content_block.get("content", [{}])[0].get("text", "")
                        break
                elif hasattr(content_block, "type") and getattr(content_block, "type") == "tool_result":
                    tool_call_id = getattr(content_block, "tool_use_id", None)
                    if getattr(content_block, "is_error", False):
                        error = getattr(content_block, "content", "Tool execution error")
                    else:
                        response = getattr(content_block, "content", "")
                    break

        # Check for OpenAI tool message format
        if hasattr(chunk, "tool_call_id") and chunk.tool_call_id:
            tool_call_id = chunk.tool_call_id
            if hasattr(chunk, "content"):
                response = chunk.content

        return tool_call_id, response, error

    def _extract_reasoning_from_data(self, reasoning_data: Dict[str, Any]) -> Optional[str]:
        """Extract reasoning content from reasoning data dict."""
        if "summary" not in reasoning_data or not reasoning_data["summary"]:
            return None

        summary = reasoning_data["summary"]

        if isinstance(summary, list):
            summary_texts = []
            for summary_item in summary:
                if isinstance(summary_item, dict):
                    if summary_item.get("type") == "summary_text":
                        summary_texts.append(summary_item.get("text", ""))
                elif isinstance(summary_item, str):
                    summary_texts.append(summary_item)
            return "\n\n".join(summary_texts) if summary_texts else None
        elif isinstance(summary, str):
            return summary

        return None

    def _extract_reasoning_from_summary(self, summary) -> Optional[str]:
        """Extract reasoning content from summary attribute."""
        if isinstance(summary, list):
            for summary_item in summary:
                if isinstance(summary_item, dict) and summary_item.get("type") == "summary_text":
                    return summary_item.get("text", "")
        elif isinstance(summary, str):
            return summary
        return None

    def _parse_content_blocks(
        self, content, existing_reasoning: Optional[str], existing_regular: Optional[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """Parse content blocks and extract reasoning/regular content."""
        reasoning_content = existing_reasoning
        regular_content = existing_regular

        if isinstance(content, list):
            # Handle structured content blocks
            for content_block in content:
                if isinstance(content_block, dict):
                    reasoning_content, regular_content = self._parse_dict_content_block(content_block, reasoning_content, regular_content)
                elif hasattr(content_block, "type"):
                    reasoning_content, regular_content = self._parse_object_content_block(content_block, reasoning_content, regular_content)
        elif isinstance(content, str):
            regular_content = content

        return reasoning_content, regular_content

    def _parse_dict_content_block(
        self, content_block: Dict[str, Any], reasoning_content: Optional[str], regular_content: Optional[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """Parse dictionary-style content block."""
        block_type = content_block.get("type")

        # Handle Anthropic thinking format
        if block_type == "thinking":
            thinking_text = content_block.get("thinking", "")
            reasoning_content = thinking_text
        # Handle Google Gemini thinking format
        elif block_type == "thinking_content":
            thinking_text = content_block.get("text", "") or content_block.get("content", "")
            reasoning_content = thinking_text
        # Handle Google thinking summaries with thought flag
        elif content_block.get("thought", False):
            thought_text = content_block.get("text", "")
            reasoning_content = thought_text
            logger.debug(f"Google thought summary found: {thought_text[:100]}...")
        # Handle OpenAI reasoning and other text formats
        else:
            text = content_block.get("text", "")

            if block_type in ["reasoning", "summary_text", "thinking_content"]:
                reasoning_content = text
            elif block_type == "text":
                regular_content = text

        return reasoning_content, regular_content

    def _parse_object_content_block(
        self, content_block, reasoning_content: Optional[str], regular_content: Optional[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """Parse object-style content block."""
        block_type = getattr(content_block, "type", None)
        text = getattr(content_block, "text", "")

        # Check for Google thought flag on object-style blocks
        thought_flag = getattr(content_block, "thought", False)
        if thought_flag:
            reasoning_content = text
            logger.debug(f"Google thought summary found (object): {text[:100]}...")
        elif block_type in ["reasoning", "summary_text", "thinking_content"]:
            reasoning_content = text
        elif block_type == "text":
            regular_content = text

        return reasoning_content, regular_content
