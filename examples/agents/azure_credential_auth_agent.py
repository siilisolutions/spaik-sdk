"""Authenticates to Azure OpenAI with Microsoft Entra ID instead of an API key.

DefaultAzureCredential picks up `az login`, a managed identity or service principal
environment variables. Set AZURE_ENDPOINT and AZURE_API_VERSION for your Azure OpenAI resource.
"""

from importlib import import_module
from typing import Callable

from dotenv import load_dotenv
from spaik_sdk import BaseAgent, LLMConfig
from spaik_sdk.models.model_registry import ModelRegistry
from spaik_sdk.models.providers.azure_provider import AzureProvider

AZURE_TOKEN_SCOPE = "https://cognitiveservices.azure.com/.default"


def create_token_provider() -> Callable[[], str]:
    azure_identity = import_module("azure.identity")
    return azure_identity.get_bearer_token_provider(azure_identity.DefaultAzureCredential(), AZURE_TOKEN_SCOPE)


def main() -> None:
    load_dotenv()
    agent = BaseAgent(
        system_prompt="You are a concise, accurate assistant.",
        llm_config=LLMConfig(
            model=ModelRegistry.GPT_6_1_SOL,
            provider=AzureProvider(azure_ad_token_provider=create_token_provider()),
            reasoning=False,
        ),
    )
    print(agent.get_response_text("In one sentence, why is keyless authentication safer than API keys?"))


if __name__ == "__main__":
    main()
