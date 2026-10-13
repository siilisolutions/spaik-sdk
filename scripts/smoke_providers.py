"""Opt-in live inference validation. Prints statuses, never credentials or provider error bodies."""

import asyncio
import os

from dotenv import load_dotenv

from spaik_sdk import BaseAgent
from spaik_sdk.models.model_registry import ModelRegistry


async def smoke(provider, model, kwargs):
    try:
        agent = BaseAgent(
            system_prompt="Reply briefly.",
            llm_model=model,
            provider=provider,
            provider_kwargs=kwargs,
            reasoning=provider != "anthropic",
        )
        text = await agent.get_response_text_async("Reply exactly OK.")
        print(
            f"{provider}: {'PASS' if text.strip() == 'OK' else 'FAIL (unexpected output)'}; invocation records={len(agent.thread_container.envelope.invocations)}"
        )
        return text.strip() == "OK"
    except Exception as error:
        detail = str(error)
        for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"]:
            secret = os.environ.get(key)
            if secret:
                detail = detail.replace(secret, "<redacted>")
        print(f"{provider}: FAIL ({type(error).__name__}): {detail[:700]}")
        return False


async def main():
    load_dotenv()
    tasks = []
    if os.environ.get("OPENAI_API_KEY") and os.environ.get("SMOKE_PROVIDER", "all") in {
        "all",
        "openai",
    }:
        tasks.append(
            smoke(
                "openai",
                ModelRegistry.GPT_6_LUNA,
                {"max_tokens": 64, "reasoning": {"effort": "none"}},
            )
        )
    if os.environ.get("ANTHROPIC_API_KEY"):
        tasks.append(
            smoke(
                "anthropic",
                ModelRegistry.CLAUDE_SONNET_5_5,
                {"max_tokens": 64, "thinking": {"type": "between_tools"}},
            )
        )
    if os.environ.get("GOOGLE_API_KEY"):
        tasks.append(
            smoke("google", ModelRegistry.GEMINI_3_8_FLASH, {"max_output_tokens": 64})
        )
    if not tasks:
        raise SystemExit("No direct provider credentials configured")
    results = await asyncio.gather(*tasks)
    if not all(results):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
