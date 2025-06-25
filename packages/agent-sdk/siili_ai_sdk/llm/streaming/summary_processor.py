from typing import Any, AsyncGenerator, List

from siili_ai_sdk.llm.streaming.block_manager import BlockManager
from siili_ai_sdk.llm.streaming.models import EventType, StreamingEvent
from siili_ai_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


class SummaryProcessor:
    """Handles processing of reasoning summaries from final outputs."""

    async def process_final_output(self, output: Any, message_id: str, block_manager: BlockManager) -> AsyncGenerator[StreamingEvent, None]:
        """Process reasoning summaries from the raw response output."""
        if not hasattr(output, "output") or not output.output:
            return

        # Look for reasoning items in the output
        for output_item in output.output:
            if hasattr(output_item, "type") and output_item.type == "reasoning":
                if hasattr(output_item, "summary") and output_item.summary:
                    summary_texts = self._extract_summary_texts(output_item.summary)

                    if summary_texts:
                        async for event in self._yield_reasoning_summary(
                            summary_texts, message_id, block_manager, "📋 **Reasoning Summary:**\n"
                        ):
                            yield event

    async def process_final_message(
        self, final_msg: Any, message_id: str, block_manager: BlockManager
    ) -> AsyncGenerator[StreamingEvent, None]:
        """Process reasoning summaries from the final message."""
        if not hasattr(final_msg, "additional_kwargs") or not final_msg.additional_kwargs:
            return

        reasoning_data = final_msg.additional_kwargs.get("reasoning")
        if not reasoning_data or "summary" not in reasoning_data or not reasoning_data["summary"]:
            return

        summary_texts = self._extract_summary_texts(reasoning_data["summary"])

        if summary_texts:
            async for event in self._yield_reasoning_summary(
                summary_texts, message_id, block_manager, "\n\n📋 **Final Reasoning Summary:**\n"
            ):
                yield event

    def _extract_summary_texts(self, summary_data: Any) -> List[str]:
        """Extract summary texts from various summary data formats."""
        summary_texts = []

        if isinstance(summary_data, list):
            for summary_item in summary_data:
                if isinstance(summary_item, dict):
                    if summary_item.get("type") == "summary_text":
                        text = summary_item.get("text", "")
                        if text:
                            summary_texts.append(text)
                elif isinstance(summary_item, str):
                    summary_texts.append(summary_item)
        elif isinstance(summary_data, str):
            summary_texts.append(summary_data)

        return summary_texts

    async def _yield_reasoning_summary(
        self, summary_texts: List[str], message_id: str, block_manager: BlockManager, prefix: str
    ) -> AsyncGenerator[StreamingEvent, None]:
        """Yield reasoning summary event."""
        summary_content = "\n\n".join(summary_texts)

        # Ensure summary block exists
        async for event in block_manager.ensure_summary_block(message_id):
            yield event

        # Yield the reasoning summary
        yield StreamingEvent(
            event_type=EventType.REASONING_SUMMARY,
            content=f"{prefix}{summary_content}",
            block_id=block_manager.get_summary_block_id(),
            message_id=message_id,
        )
