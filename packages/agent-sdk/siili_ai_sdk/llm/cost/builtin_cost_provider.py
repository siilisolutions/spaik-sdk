from siili_ai_sdk.llm.consumption.token_usage import TokenUsage
from siili_ai_sdk.llm.cost.cost_provider import CostProvider
from siili_ai_sdk.models.llm_model import LLMModel


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
            # Claude 4 Sonnet: $3.00 input, $15.00 output per 1M tokens
            return TokenUsage(input_tokens=300, output_tokens=1500, reasoning_tokens=0, cache_creation_tokens=375, cache_read_tokens=30)
        elif name.startswith("claude-opus-4") or name.startswith("claude-4-opus"):
            # Claude 4 Opus: $15.00 input, $75.00 output per 1M tokens
            return TokenUsage(input_tokens=1500, output_tokens=7500, reasoning_tokens=0, cache_creation_tokens=1875, cache_read_tokens=150)

        # OpenAI models
        elif name.startswith("gpt-4.1"):
            # GPT-4.1: $2.00 input, $8.00 output per 1M tokens
            return TokenUsage(input_tokens=200, output_tokens=800, reasoning_tokens=0, cache_creation_tokens=250, cache_read_tokens=20)
        elif name.startswith("gpt-4o"):
            # GPT-4o: $2.50 input, $10.00 output per 1M tokens
            return TokenUsage(input_tokens=250, output_tokens=1000, reasoning_tokens=0, cache_creation_tokens=312, cache_read_tokens=25)
        elif name.startswith("o4-mini"):
            # O4-mini: $0.40 input, $1.60 output per 1M tokens (based on GPT-4.1-mini pricing)
            return TokenUsage(
                input_tokens=40,
                output_tokens=160,
                reasoning_tokens=440,  # 110% markup for reasoning tokens
                cache_creation_tokens=50,
                cache_read_tokens=4,
            )
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
        elif name.startswith("gemini-2.5-flash"):
            # Gemini 2.5 Flash: $0.15 input, $0.60 output per 1M tokens
            return TokenUsage(input_tokens=15, output_tokens=60, reasoning_tokens=0, cache_creation_tokens=19, cache_read_tokens=1)
        elif name.startswith("gemini-2.5-pro"):
            # Gemini 2.5 Pro: $1.25 input, $10.00 output per 1M tokens
            return TokenUsage(input_tokens=125, output_tokens=1000, reasoning_tokens=0, cache_creation_tokens=156, cache_read_tokens=12)

        # Default fallback for unknown models
        else:
            return TokenUsage(input_tokens=0, output_tokens=0, reasoning_tokens=0, cache_creation_tokens=0, cache_read_tokens=0)
