import pytest

from spaik_sdk.llm.cost.builtin_cost_provider import BuiltinCostProvider
from spaik_sdk.models.model_registry import ModelRegistry


@pytest.mark.unit
class TestBuiltinCostProvider:
    @pytest.mark.parametrize(
        "model,expected_input,expected_output,expected_cache_read",
        [
            (ModelRegistry.CLAUDE_4_7_OPUS, 500, 2500, 50),
            (ModelRegistry.GPT_5_4_NANO, 20, 125, 2),
            (ModelRegistry.GPT_5_5, 500, 3000, 50),
            (ModelRegistry.GPT_5_5_PRO, 3000, 18000, 0),
            (ModelRegistry.GEMINI_3_FLASH, 50, 300, 5),
            (ModelRegistry.GEMINI_3_1_PRO, 200, 1200, 20),
        ],
    )
    def test_latest_model_pricing(self, model, expected_input: int, expected_output: int, expected_cache_read: int):
        pricing = BuiltinCostProvider().get_token_pricing(model)

        assert pricing.input_tokens == expected_input
        assert pricing.output_tokens == expected_output
        assert pricing.cache_read_tokens == expected_cache_read
