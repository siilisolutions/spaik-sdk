from dotenv import load_dotenv
from spaik_sdk import BaseAgent


class HelloAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(system_prompt="You are a concise, accurate assistant. Answer in plain language and keep replies short.")


if __name__ == "__main__":
    load_dotenv()
    agent = HelloAgent()
    print(agent.get_response_text("Explain in two sentences what an AI agent is."))
