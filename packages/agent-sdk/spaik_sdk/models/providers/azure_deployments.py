import os
from typing import Collection, Dict, Set

from spaik_sdk.models.llm_model import LLMModel
from spaik_sdk.models.model_registry import ModelRegistry

AZURE_DEPLOYMENT_ENV_VARS: Dict[str, str] = {
    "claude-opus-4-7": "AZURE_CLAUDE_OPUS_4_7_DEPLOYMENT",
    "claude-opus-4-6": "AZURE_CLAUDE_OPUS_4_6_DEPLOYMENT",
    "claude-sonnet-4-6": "AZURE_CLAUDE_SONNET_4_6_DEPLOYMENT",
    "gpt-4.1": "AZURE_GPT_4_1_DEPLOYMENT",
    "gpt-4.1-mini": "AZURE_GPT_4_1_MINI_DEPLOYMENT",
    "gpt-4.1-nano": "AZURE_GPT_4_1_NANO_DEPLOYMENT",
    "gpt-4o": "AZURE_GPT_4O_DEPLOYMENT",
    "gpt-4o-mini": "AZURE_GPT_4O_MINI_DEPLOYMENT",
    "o1": "AZURE_O1_DEPLOYMENT",
    "o1-mini": "AZURE_O1_MINI_DEPLOYMENT",
    "o1-pro": "AZURE_O1_PRO_DEPLOYMENT",
    "o3": "AZURE_O3_DEPLOYMENT",
    "o3-mini": "AZURE_O3_MINI_DEPLOYMENT",
    "o3-pro": "AZURE_O3_PRO_DEPLOYMENT",
    "o4-mini": "AZURE_O4_MINI_DEPLOYMENT",
    "o4-mini-2025-04-16": "AZURE_O4_MINI_2025_04_16_DEPLOYMENT",
    "gpt-5": "AZURE_GPT_5_DEPLOYMENT",
    "gpt-5-mini": "AZURE_GPT_5_MINI_DEPLOYMENT",
    "gpt-5-nano": "AZURE_GPT_5_NANO_DEPLOYMENT",
    "gpt-5-chat-latest": "AZURE_GPT_5_CHAT_DEPLOYMENT",
    "gpt-5-codex": "AZURE_GPT_5_CODEX_DEPLOYMENT",
    "gpt-5-pro": "AZURE_GPT_5_PRO_DEPLOYMENT",
    "gpt-5.1": "AZURE_GPT_5_1_DEPLOYMENT",
    "gpt-5.1-chat-latest": "AZURE_GPT_5_1_CHAT_DEPLOYMENT",
    "gpt-5.1-codex": "AZURE_GPT_5_1_CODEX_DEPLOYMENT",
    "gpt-5.1-codex-mini": "AZURE_GPT_5_1_CODEX_MINI_DEPLOYMENT",
    "gpt-5.1-codex-max": "AZURE_GPT_5_1_CODEX_MAX_DEPLOYMENT",
    "gpt-5.2": "AZURE_GPT_5_2_DEPLOYMENT",
    "gpt-5.2-chat-latest": "AZURE_GPT_5_2_CHAT_DEPLOYMENT",
    "gpt-5.2-codex": "AZURE_GPT_5_2_CODEX_DEPLOYMENT",
    "gpt-5.2-pro": "AZURE_GPT_5_2_PRO_DEPLOYMENT",
    "gpt-5.3-codex": "AZURE_GPT_5_3_CODEX_DEPLOYMENT",
    "gpt-5.3-chat-latest": "AZURE_GPT_5_3_CHAT_DEPLOYMENT",
    "gpt-5.4": "AZURE_GPT_5_4_DEPLOYMENT",
    "gpt-5.4-pro": "AZURE_GPT_5_4_PRO_DEPLOYMENT",
    "gpt-5.4-mini": "AZURE_GPT_5_4_MINI_DEPLOYMENT",
    "gpt-5.4-nano": "AZURE_GPT_5_4_NANO_DEPLOYMENT",
    "gpt-5.5": "AZURE_GPT_5_5_DEPLOYMENT",
    "DeepSeek-V3-0324": "AZURE_DEEPSEEK_V3_DEPLOYMENT",
    "DeepSeek-V3.1": "AZURE_DEEPSEEK_V3_1_DEPLOYMENT",
    "DeepSeek-V3.2": "AZURE_DEEPSEEK_V3_2_DEPLOYMENT",
    "DeepSeek-V3.2-Speciale": "AZURE_DEEPSEEK_V3_2_SPECIALE_DEPLOYMENT",
    "DeepSeek-R1": "AZURE_DEEPSEEK_R1_DEPLOYMENT",
    "DeepSeek-R1-0528": "AZURE_DEEPSEEK_R1_0528_DEPLOYMENT",
    "Mistral-Large-3": "AZURE_MISTRAL_LARGE_3_DEPLOYMENT",
    "Llama-4-Maverick-17B-128E-Instruct-FP8": "AZURE_LLAMA_4_MAVERICK_DEPLOYMENT",
    "Llama-3.3-70B-Instruct": "AZURE_LLAMA_3_3_70B_DEPLOYMENT",
    "Cohere-command-a": "AZURE_COHERE_COMMAND_A_DEPLOYMENT",
    "grok-3": "AZURE_GROK_3_DEPLOYMENT",
    "grok-3-mini": "AZURE_GROK_3_MINI_DEPLOYMENT",
    "grok-4": "AZURE_GROK_4_DEPLOYMENT",
    "grok-4-fast-reasoning": "AZURE_GROK_4_FAST_REASONING_DEPLOYMENT",
    "grok-4-fast-non-reasoning": "AZURE_GROK_4_FAST_NON_REASONING_DEPLOYMENT",
    "grok-code-fast-1": "AZURE_GROK_CODE_FAST_1_DEPLOYMENT",
    "Kimi-K2-Thinking": "AZURE_KIMI_K2_THINKING_DEPLOYMENT",
}


def get_azure_supported_models() -> Collection[LLMModel]:
    supported: Set[LLMModel] = set()
    for model_name in AZURE_DEPLOYMENT_ENV_VARS:
        try:
            supported.add(ModelRegistry.from_name(model_name))
        except ValueError:
            pass
    return supported


def get_deployment_name(model_name: str) -> str:
    env_var = AZURE_DEPLOYMENT_ENV_VARS.get(model_name)
    if not env_var:
        raise ValueError(f"Model '{model_name}' not supported on Azure. Add it to AZURE_DEPLOYMENT_ENV_VARS.")
    return os.environ.get(env_var, model_name)


def get_required_env(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise ValueError(f"Environment variable {key} is required but not set")
    return value
