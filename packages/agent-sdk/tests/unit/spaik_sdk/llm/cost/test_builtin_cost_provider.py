from datetime import date

import pytest

import spaik_sdk.llm.cost.builtin_cost_provider as builtin_cost_provider
from spaik_sdk.llm.consumption.token_usage import TokenUsage
from spaik_sdk.llm.cost.builtin_cost_provider import BuiltinCostProvider
from spaik_sdk.models.model_registry import ModelRegistry


class DateAt(date):
    current_date = date.min

    @classmethod
    def today(cls) -> date:
        return cls.current_date


@pytest.mark.unit
class TestBuiltinCostProvider:
    @pytest.mark.parametrize(
        "model,expected_input,expected_output,expected_cache_read",
        [
            (ModelRegistry.CLAUDE_4_8_OPUS, 500, 2500, 50),
            (ModelRegistry.CLAUDE_FABLE_5, 1000, 5000, 100),
            (ModelRegistry.CLAUDE_OPUS_5, 500, 2500, 50),
            (ModelRegistry.GPT_5_6_SOL, 500, 3000, 50),
            (ModelRegistry.GPT_5_6_TERRA, 250, 1500, 25),
            (ModelRegistry.GPT_5_6_LUNA, 100, 600, 10),
            (ModelRegistry.GPT_5_4_NANO, 20, 125, 2),
            (ModelRegistry.GPT_5_5, 500, 3000, 50),
            (ModelRegistry.GPT_5_5_PRO, 3000, 18000, 0),
            (ModelRegistry.GEMINI_3_FLASH, 50, 300, 5),
            (ModelRegistry.GEMINI_3_5_FLASH, 150, 900, 15),
            (ModelRegistry.GEMINI_3_5_FLASH_LITE, 30, 250, 3),
            (ModelRegistry.GEMINI_3_6_FLASH, 150, 750, 15),
            (ModelRegistry.GEMINI_3_1_PRO, 200, 1200, 20),
            (ModelRegistry.GEMINI_3_1_FLASH_LITE, 25, 150, 2),
        ],
    )
    def test_latest_model_pricing(self, model, expected_input: int, expected_output: int, expected_cache_read: int):
        pricing = BuiltinCostProvider().get_token_pricing(model)

        assert pricing.input_tokens == expected_input
        assert pricing.output_tokens == expected_output
        assert pricing.cache_read_tokens == expected_cache_read

    @pytest.mark.parametrize(
        "current_date,expected",
        [
            (date(2026, 8, 31), TokenUsage(200, 1000, reasoning_tokens=0, cache_creation_tokens=250, cache_read_tokens=20)),
            (date(2026, 9, 1), TokenUsage(300, 1500, reasoning_tokens=0, cache_creation_tokens=375, cache_read_tokens=30)),
        ],
    )
    def test_claude_sonnet_5_pricing_uses_effective_date(self, monkeypatch, current_date: date, expected: TokenUsage):
        DateAt.current_date = current_date
        monkeypatch.setattr(builtin_cost_provider, "date", DateAt)

        pricing = BuiltinCostProvider().get_token_pricing(ModelRegistry.CLAUDE_SONNET_5)

        assert pricing == expected
