from spaik_sdk.llm.consumption.token_usage import TokenUsage
from spaik_sdk.llm.cost.cost_provider import CostProvider
from spaik_sdk.models.llm_model import LLMModel


class BuiltinCostProvider(CostProvider):
    def get_token_pricing(self, model: LLMModel) -> TokenUsage:
        """Get token pricing in USD cents per million tokens."""
        name = model.name

        # Anthropic Claude models
        if name.startswith("claude-3-7-sonnet"):
            # Claude 3.7 Sonnet: $3.00 input, $15.00 output per 1M tokens
            return TokenUsage(
                input_tokens=300,  # $3.00 in cents per 1M tokens
                output_tokens=1500,  # $15.00 in cents per 1M tokens
                reasoning_tokens=0,
                cache_creation_tokens=375,  # 25% markup on input for cache creation
                cache_read_tokens=30,  # 10% of input cost for cache reads
            )
        elif name.startswith("claude-sonnet-4") or name.startswith("claude-4-sonnet"):
            # Claude 4 Sonnet (all versions): $3.00 input, $15.00 output per 1M tokens
            return TokenUsage(input_tokens=300, output_tokens=1500, reasoning_tokens=0, cache_creation_tokens=375, cache_read_tokens=30)
        elif name.startswith("claude-opus-4-5") or name.startswith("claude-opus-4-6") or name.startswith("claude-opus-4-7"):
            # Claude Opus 4.5 / 4.6 / 4.7: $5.00 input, $25.00 output per 1M tokens
            return TokenUsage(input_tokens=500, output_tokens=2500, reasoning_tokens=0, cache_creation_tokens=625, cache_read_tokens=50)
        elif name.startswith("claude-opus-4") or name.startswith("claude-4-opus"):
            # Claude Opus 4 / 4.1: $15.00 input, $75.00 output per 1M tokens
            return TokenUsage(input_tokens=1500, output_tokens=7500, reasoning_tokens=0, cache_creation_tokens=1875, cache_read_tokens=150)

        # OpenAI models — legacy (deprecated on OpenAI direct API, still available on Azure)
        elif name.startswith("gpt-4.1"):
            # GPT-4.1: $2.00 input, $8.00 output per 1M tokens
            return TokenUsage(input_tokens=200, output_tokens=800, reasoning_tokens=0, cache_creation_tokens=250, cache_read_tokens=20)
        elif name.startswith("gpt-4o"):
            # GPT-4o: $2.50 input, $10.00 output per 1M tokens
            return TokenUsage(input_tokens=250, output_tokens=1000, reasoning_tokens=0, cache_creation_tokens=312, cache_read_tokens=25)
        elif name.startswith("o1-pro"):
            # O1-Pro: $150.00 input, $600.00 output per 1M tokens
            return TokenUsage(input_tokens=15000, output_tokens=60000, reasoning_tokens=0, cache_creation_tokens=0, cache_read_tokens=0)
        elif name.startswith("o4-mini"):
            # O4-mini: $0.40 input, $1.60 output per 1M tokens
            return TokenUsage(
                input_tokens=40,
                output_tokens=160,
                reasoning_tokens=440,  # 110% markup for reasoning tokens
                cache_creation_tokens=50,
                cache_read_tokens=4,
            )

        # OpenAI models — current
        elif name.startswith("gpt-5.5-pro"):
            # GPT-5.5 Pro: $30.00 input, $180.00 output per 1M tokens
            return TokenUsage(input_tokens=3000, output_tokens=18000, reasoning_tokens=18000, cache_creation_tokens=0, cache_read_tokens=0)
        elif name.startswith("gpt-5.5"):
            # GPT-5.5: $5.00 input, $30.00 output per 1M tokens
            return TokenUsage(input_tokens=500, output_tokens=3000, reasoning_tokens=3000, cache_creation_tokens=625, cache_read_tokens=50)
        elif name.startswith("gpt-5.4-pro"):
            # GPT-5.4 Pro: $30.00 input, $180.00 output per 1M tokens
            return TokenUsage(input_tokens=3000, output_tokens=18000, reasoning_tokens=18000, cache_creation_tokens=0, cache_read_tokens=0)
        elif name.startswith("gpt-5.4-nano"):
            # GPT-5.4 Nano: $0.20 input, $1.25 output per 1M tokens
            return TokenUsage(input_tokens=20, output_tokens=125, reasoning_tokens=125, cache_creation_tokens=25, cache_read_tokens=2)
        elif name.startswith("gpt-5.4-mini"):
            # GPT-5.4 Mini: $0.75 input, $4.50 output per 1M tokens
            return TokenUsage(input_tokens=75, output_tokens=450, reasoning_tokens=450, cache_creation_tokens=94, cache_read_tokens=7)
        elif name.startswith("gpt-5.4"):
            # GPT-5.4: $2.50 input, $15.00 output per 1M tokens
            return TokenUsage(input_tokens=250, output_tokens=1500, reasoning_tokens=1500, cache_creation_tokens=312, cache_read_tokens=25)
        elif name.startswith("gpt-5"):
            if "nano" in name:
                # GPT-5 Nano: $0.05 input, $0.40 output per 1M tokens
                return TokenUsage(
                    input_tokens=5,
                    output_tokens=40,
                    reasoning_tokens=44,  # 10% markup for reasoning
                    cache_creation_tokens=6,  # 25% markup on input for cache creation
                    cache_read_tokens=0,  # 90% discount: $0.005 per 1M tokens
                )
            elif "mini" in name:
                # GPT-5 Mini: $0.25 input, $2.00 output per 1M tokens
                return TokenUsage(
                    input_tokens=25,
                    output_tokens=200,
                    reasoning_tokens=220,  # 10% markup for reasoning
                    cache_creation_tokens=31,  # 25% markup on input for cache creation
                    cache_read_tokens=2,  # 90% discount: $0.025 per 1M tokens
                )
            else:
                # GPT-5: $1.25 input, $10.00 output per 1M tokens
                return TokenUsage(
                    input_tokens=125,
                    output_tokens=1000,
                    reasoning_tokens=1100,  # 10% markup for reasoning
                    cache_creation_tokens=156,  # 25% markup on input for cache creation
                    cache_read_tokens=12,  # 90% discount: $0.125 per 1M tokens
                )

        # Google Gemini models
        elif name.startswith("gemini-2.5-flash-lite"):
            # Gemini 2.5 Flash-Lite: $0.05 input, $0.20 output per 1M tokens
            return TokenUsage(input_tokens=5, output_tokens=20, reasoning_tokens=0, cache_creation_tokens=6, cache_read_tokens=0)
        elif name.startswith("gemini-2.5-flash"):
            # Gemini 2.5 Flash: $0.15 input, $0.60 output per 1M tokens
            return TokenUsage(input_tokens=15, output_tokens=60, reasoning_tokens=0, cache_creation_tokens=19, cache_read_tokens=1)
        elif name.startswith("gemini-2.5-pro"):
            # Gemini 2.5 Pro: $1.25 input, $10.00 output per 1M tokens
            return TokenUsage(input_tokens=125, output_tokens=1000, reasoning_tokens=0, cache_creation_tokens=156, cache_read_tokens=12)
        elif name.startswith("gemini-3.1-pro"):
            # Gemini 3.1 Pro: $2.00 input, $12.00 output per 1M tokens for prompts <= 200k tokens
            return TokenUsage(input_tokens=200, output_tokens=1200, reasoning_tokens=0, cache_creation_tokens=250, cache_read_tokens=20)
        elif name.startswith("gemini-3.1-flash-lite"):
            # Gemini 3.1 Flash-Lite: $0.25 input, $1.50 output per 1M tokens
            return TokenUsage(input_tokens=25, output_tokens=150, reasoning_tokens=0, cache_creation_tokens=31, cache_read_tokens=2)
        elif name.startswith("gemini-3-pro"):
            # Gemini 3 Pro: $1.25 input, $10.00 output per 1M tokens (deprecated on Google API March 9, 2026)
            return TokenUsage(input_tokens=125, output_tokens=1000, reasoning_tokens=0, cache_creation_tokens=156, cache_read_tokens=12)
        elif name.startswith("gemini-3-flash"):
            # Gemini 3 Flash: $0.50 input, $3.00 output per 1M tokens
            return TokenUsage(input_tokens=50, output_tokens=300, reasoning_tokens=0, cache_creation_tokens=62, cache_read_tokens=5)

        # Default fallback for unknown models
        else:
            return TokenUsage(input_tokens=0, output_tokens=0, reasoning_tokens=0, cache_creation_tokens=0, cache_read_tokens=0)
