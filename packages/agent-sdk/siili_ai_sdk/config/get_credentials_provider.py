from siili_ai_sdk.config.credentials_provider import CredentialsProvider
from siili_ai_sdk.config.env import env_config
from siili_ai_sdk.config.env_credentials_provider import EnvCredentialsProvider


def get_credentials_provider() -> CredentialsProvider:
    provider_type = env_config.get_credentials_provider_type()
    if provider_type == "env":
        return EnvCredentialsProvider()
    else:
        raise ValueError(f"Unsupported provider type: {provider_type}")


credentials_provider = get_credentials_provider()
