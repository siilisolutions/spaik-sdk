from importlib import import_module
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv
from spaik_sdk.agent.base_agent import BaseAgent
from spaik_sdk.models.llm_config import LLMConfig
from spaik_sdk.models.model_registry import ModelRegistry
from spaik_sdk.models.providers.azure_provider import AzureProvider

AZURE_TOKEN_SCOPE = "https://cognitiveservices.azure.com/.default"


class AzureCredentialAuthAgent(BaseAgent):
    pass


def create_token_provider() -> Callable[[], str]:
    azure_identity = import_module("azure.identity")
    return azure_identity.get_bearer_token_provider(azure_identity.DefaultAzureCredential(), AZURE_TOKEN_SCOPE)


def main() -> None:
    script_path = Path(__file__).resolve()
    load_dotenv(script_path.parents[2] / ".env")
    load_dotenv(script_path.parents[1] / ".env")

    agent = AzureCredentialAuthAgent(
        system_prompt="You are a concise assistant.",
        llm_config=LLMConfig(
            model=ModelRegistry.GPT_4_1_MINI,
            provider=AzureProvider(azure_ad_token_provider=create_token_provider()),
            reasoning=False,
            tool_usage=False,
            temperature=0,
        ),
    )

    print(agent.get_response_text("Reply with sentence describing cats."))


if __name__ == "__main__":
    main()
