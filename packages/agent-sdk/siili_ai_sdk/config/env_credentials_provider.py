import os
from siili_ai_sdk.config.credentials_provider import CredentialsProvider
from siili_ai_sdk.config.env import env_config


class EnvCredentialsProvider(CredentialsProvider):
    def get_key(self, key: str) -> str:
        return env_config.get_key(key, required=True)