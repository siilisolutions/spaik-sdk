from typing import Any, Dict, Optional

from siili_ai_sdk.llm.consumption.consumption_estimate import ConsumptionEstimate
from siili_ai_sdk.llm.consumption.token_usage import TokenUsage
from siili_ai_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


class ConsumptionEstimateBuilder:
    """Builder for creating consumption estimates from various data sources."""

    def __init__(self):
        self._token_usage: Optional[TokenUsage] = None
        self._metadata: Dict[str, Any] = {}

    def from_usage_metadata(self, usage_metadata: Dict[str, Any]) -> "ConsumptionEstimateBuilder":
        """Extract consumption data from LangChain usage_metadata."""

        logger.info(f"usage_metadata: {usage_metadata}")
        if not usage_metadata:
            return self

        # Extract basic token counts
        input_tokens = usage_metadata.get("input_tokens", 0)
        output_tokens = usage_metadata.get("output_tokens", 0)
        total_tokens = usage_metadata.get("total_tokens", 0)

        # Extract reasoning tokens (Google/OpenAI)
        reasoning_tokens = 0
        output_token_details = usage_metadata.get("output_token_details")
        if output_token_details:
            reasoning_tokens = output_token_details.get("reasoning", 0)

        # Extract cache tokens (Anthropic)
        cache_creation_tokens = 0
        cache_read_tokens = 0
        input_token_details = usage_metadata.get("input_token_details")
        if input_token_details:
            cache_creation_tokens = input_token_details.get("cache_creation", 0)
            cache_read_tokens = input_token_details.get("cache_read", 0)

        self._token_usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            reasoning_tokens=reasoning_tokens,
            cache_creation_tokens=cache_creation_tokens,
            cache_read_tokens=cache_read_tokens,
        )

        logger.info(f"self._token_usage: {self._token_usage}")
        return self

    def from_response_metadata(self, response_metadata: Any) -> "ConsumptionEstimateBuilder":
        """Extract consumption data from response_metadata when usage_metadata is unavailable."""
        if not response_metadata:
            return self

        # Store metadata for potential estimation
        self._metadata.update(
            {
                "finish_reason": getattr(response_metadata, "finish_reason", None),
                "stop_reason": getattr(response_metadata, "stop_reason", None),
                "response_id": getattr(response_metadata, "id", None),
            }
        )

        return self

    def from_event_metadata(self, metadata: Dict[str, Any]) -> "ConsumptionEstimateBuilder":
        """Extract relevant info from LangChain event metadata."""
        if not metadata:
            return self

        # Store any potentially useful metadata
        self._metadata.update(
            {
                "ls_provider": metadata.get("ls_provider"),
                "ls_model_name": metadata.get("ls_model_name"),
            }
        )

        return self

    def estimate_from_content(self, content: str) -> "ConsumptionEstimateBuilder":
        """Rough estimation when no usage metadata is available."""
        if not content or self._token_usage:
            return self

        # Very rough token estimation (4 chars per token average)
        estimated_output_tokens = len(content) // 4
        estimated_input_tokens = estimated_output_tokens * 5

        self._token_usage = TokenUsage(
            input_tokens=estimated_input_tokens,
            output_tokens=estimated_output_tokens,
            total_tokens=estimated_output_tokens,
        )

        self._metadata["estimation_method"] = "content_length"

        return self

    def build(self) -> Optional[ConsumptionEstimate]:
        """Build the final ConsumptionEstimate."""
        if not self._token_usage:
            return None

        return ConsumptionEstimate(
            token_usage=self._token_usage,
            metadata=self._metadata,
        )
