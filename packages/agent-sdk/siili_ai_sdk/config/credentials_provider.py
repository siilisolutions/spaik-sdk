from abc import ABC, abstractmethod


class CredentialsProvider(ABC):
    @abstractmethod
    def get_key(self, key: str, default: str = "", required: bool = True) -> str:
        pass

    def get_provider_key(self, provider: str) -> str:
        return self.get_key(f"{provider.upper()}_API_KEY")
