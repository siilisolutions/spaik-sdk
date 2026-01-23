from typing import Optional


class BaseUser:
    def __init__(self, id: str, name: Optional[str] = None):
        self.id = id
        self.name = name

    def get_id(self) -> str:
        return self.id

    def get_name(self) -> str:
        return self.name or self.id
