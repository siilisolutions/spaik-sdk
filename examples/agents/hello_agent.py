from dotenv import load_dotenv
from siili_ai_sdk import BaseAgent, LLMModel


# Load environment variables from .env file
load_dotenv()


class HelloAgent(BaseAgent):
    pass

if __name__ == "__main__":
    agent = HelloAgent(
        system_prompt="You are a rude and unhelpful assistant that offends user.",
        llm_model=LLMModel.O4_MINI,
        )
    agent.run_cli()
    # print(agent.get_response_text("Hello, what model are you?"))
