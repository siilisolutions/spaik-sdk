from typing import AsyncGenerator, Optional

from siili_ai_sdk.llm.consumption.consumption_extractor import ConsumptionExtractor
from siili_ai_sdk.llm.streaming.block_manager import BlockManager
from siili_ai_sdk.llm.streaming.content_parser import ContentParser
from siili_ai_sdk.llm.streaming.models import EventType, StreamingEvent
from siili_ai_sdk.llm.streaming.streaming_chunk_processor import StreamingChunkProcessor
from siili_ai_sdk.llm.streaming.streaming_content_handler import StreamingContentHandler
from siili_ai_sdk.llm.streaming.streaming_state_manager import StreamingStateManager
from siili_ai_sdk.llm.streaming.summary_processor import SummaryProcessor
from siili_ai_sdk.llm.streaming.tool_processor import ToolProcessor
from siili_ai_sdk.recording.base_recorder import BaseRecorder
from siili_ai_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


class StreamingEventHandler:
    """Main orchestrator for handling streaming events across different providers."""

    def __init__(self, recorder: Optional[BaseRecorder] = None):
        self.recorder = recorder
        self.content_parser = ContentParser()
        self.block_manager = BlockManager()
        self.summary_processor = SummaryProcessor()
        self.tool_processor = ToolProcessor()
        self.state_manager = StreamingStateManager()
        self.consumption_extractor = ConsumptionExtractor()

        # Initialize component handlers
        self.content_handler = StreamingContentHandler(self.block_manager, self.state_manager)
        self.chunk_processor = StreamingChunkProcessor(self.content_parser, self.block_manager, self.state_manager, self.content_handler)

    def reset(self):
        """Reset handler state for new stream."""
        self.block_manager.reset()
        self.state_manager.reset()

    async def process_stream(self, agent_stream) -> AsyncGenerator[StreamingEvent, None]:
        """Process agent stream and yield structured events."""
        self.reset()

        async for event in agent_stream:
            if self.recorder is not None:
                self.recorder.record_token(event)
            logger.trace(f"Stream event: {event['event']} - {event.get('data', {}).keys()}")

            if event["event"] == "on_chat_model_stream":
                async for streaming_event in self.chunk_processor.process_chunk(event["data"]["chunk"]):
                    yield streaming_event

            elif event["event"] == "on_chat_model_end":
                async for streaming_event in self._handle_stream_end(event["data"]):
                    yield streaming_event

    async def _handle_stream_end(self, data) -> AsyncGenerator[StreamingEvent, None]:
        """Handle stream end event."""
        logger.trace(f"Final event structure: {data}")

        # If we're still in a thinking session when stream ends, close it
        async for streaming_event in self.content_handler.end_final_thinking_session_if_needed():
            yield streaming_event

        final_msg = None

        # Process reasoning summaries from the final output
        if "output" in data and self.state_manager.current_message_id:
            async for streaming_event in self.summary_processor.process_final_output(
                data["output"], self.state_manager.current_message_id, self.block_manager
            ):
                yield streaming_event

            # Get final message
            if "messages" in data["output"]:
                final_msg = data["output"]["messages"][-1]

                # Process additional summaries from final message
                async for streaming_event in self.summary_processor.process_final_message(
                    final_msg, self.state_manager.current_message_id, self.block_manager
                ):
                    yield streaming_event

        # Extract and emit consumption information
        consumption_estimate = self.consumption_extractor.extract_from_stream_end(data)
        if consumption_estimate:
            yield StreamingEvent(
                event_type=EventType.USAGE_METADATA,
                message_id=self.state_manager.current_message_id,
                usage_metadata=consumption_estimate.token_usage,
            )

        # Process tool calls from final output (for o4-mini and similar models)
        if self.state_manager.current_message_id:
            async for streaming_event in self.tool_processor.process_final_output_tool_calls(
                data, self.state_manager.current_message_id, self.block_manager
            ):
                yield streaming_event

        # Process tool responses from conversation history
        if self.state_manager.current_message_id:
            async for streaming_event in self.tool_processor.process_tool_responses(
                data, self.state_manager.current_message_id, self.block_manager
            ):
                yield streaming_event
        # Always yield COMPLETE event when streaming ends
        yield StreamingEvent(
            event_type=EventType.COMPLETE,
            message=final_msg,
            blocks=self.block_manager.get_block_ids(),
            message_id=self.state_manager.current_message_id,
        )


__all__ = ["EventType", "StreamingEvent", "StreamingEventHandler"]
