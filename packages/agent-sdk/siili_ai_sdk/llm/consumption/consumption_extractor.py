from typing import Any, Dict, Optional

from siili_ai_sdk.llm.consumption.consumption_estimate import ConsumptionEstimate
from siili_ai_sdk.llm.consumption.consumption_estimate_builder import ConsumptionEstimateBuilder
from siili_ai_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


class ConsumptionExtractor:
    """Extracts consumption information from LangChain streaming events."""

    def extract_from_stream_end(self, data: Dict[str, Any]) -> Optional[ConsumptionEstimate]:
        """Extract consumption data from on_chat_model_end event data."""
        builder = ConsumptionEstimateBuilder()

        # Extract from event metadata if available
        if "metadata" in data:
            builder.from_event_metadata(data["metadata"])

        # Extract from output data
        if "output" in data:
            output = data["output"]

            # Try usage_metadata first (preferred)
            usage_metadata = getattr(output, "usage_metadata", None)
            if usage_metadata:
                usage_metadata = dict(usage_metadata)
                builder.from_usage_metadata(usage_metadata)
            else:
                # Fallback to response_metadata
                response_metadata = getattr(output, "response_metadata", None)
                if response_metadata:
                    builder.from_response_metadata(response_metadata)

                # Last resort: estimate from content
                content = getattr(output, "content", "")
                if isinstance(content, str):
                    builder.estimate_from_content(content)

        consumption_estimate = builder.build()

        if consumption_estimate:
            cache_info = ""
            if consumption_estimate.token_usage.cache_creation_tokens > 0 or consumption_estimate.token_usage.cache_read_tokens > 0:
                cache_info = (
                    f", cache_create: {consumption_estimate.token_usage.cache_creation_tokens}, "
                    f"cache_read: {consumption_estimate.token_usage.cache_read_tokens}"
                )

            logger.info(
                f"📊 Consumption tracking - "
                f"Tokens: {consumption_estimate.token_usage.total_tokens} "
                f"(in: {consumption_estimate.token_usage.input_tokens}, out: {consumption_estimate.token_usage.output_tokens}, "
                f"reasoning: {consumption_estimate.token_usage.reasoning_tokens}{cache_info})"
            )
            logger.debug(f"📊 Full consumption data: {consumption_estimate.to_dict()}")

        return consumption_estimate
