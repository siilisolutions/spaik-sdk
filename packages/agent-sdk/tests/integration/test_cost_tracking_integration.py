"""Integration test for cost tracking in streaming events."""

import pytest

from siili_ai_sdk.llm.consumption.consumption_extractor import ConsumptionExtractor


@pytest.mark.integration
class TestCostTrackingIntegration:
    """Test consumption extraction from various LLM response formats."""

    def test_consumption_extractor_with_openai_style_data(self):
        """Test consumption extraction with OpenAI-style usage metadata."""
        extractor = ConsumptionExtractor()

        class MockOutput:
            usage_metadata = {
                "input_tokens": 100,
                "output_tokens": 50,
                "total_tokens": 150,
            }
            response_metadata = {"model_name": "gpt-4o"}

        data = {
            "metadata": {"ls_provider": "openai", "ls_model_name": "gpt-4o"},
            "output": MockOutput(),
        }

        result = extractor.extract_from_stream_end(data)

        assert result is not None
        assert result.token_usage.input_tokens == 100
        assert result.token_usage.output_tokens == 50
        assert result.token_usage.total_tokens == 150

    def test_consumption_extractor_with_google_style_data(self):
        """Test consumption extraction with Google-style usage metadata including reasoning tokens."""
        extractor = ConsumptionExtractor()

        class MockOutput:
            usage_metadata = {
                "input_tokens": 53,
                "output_tokens": 11,
                "total_tokens": 110,
                "output_token_details": {"reasoning": 25},
            }
            response_metadata = {"model_name": "gemini-2.5-flash"}

        data = {
            "metadata": {"ls_provider": "google_genai", "ls_model_name": "gemini-2.5-flash"},
            "output": MockOutput(),
        }

        result = extractor.extract_from_stream_end(data)

        assert result is not None
        assert result.token_usage.input_tokens == 53
        assert result.token_usage.output_tokens == 11
        assert result.token_usage.reasoning_tokens == 25

    def test_consumption_extractor_fallback_estimation(self):
        """Test consumption extraction fallback when usage_metadata is not available."""
        extractor = ConsumptionExtractor()

        class MockOutput:
            usage_metadata = None
            response_metadata = {"model_name": "gpt-4.1-2025-04-14"}
            content = "This is a test response from GPT-4.1"

        data = {
            "metadata": {"ls_provider": "openai", "ls_model_name": "gpt-4.1"},
            "output": MockOutput(),
        }

        result = extractor.extract_from_stream_end(data)

        assert result is not None
        assert result.token_usage.output_tokens > 0
        assert result.metadata.get("estimation_method") == "content_length"
