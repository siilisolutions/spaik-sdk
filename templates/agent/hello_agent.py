from dotenv import load_dotenv

from siili_ai_sdk.agent.base_agent import BaseAgent



class HelloAgent(BaseAgent):
    def __init__(self):
        super().__init__(system_prompt="You're an unhelpful assistant that cant resist constantly talking about cats.")

if __name__ == "__main__":
    load_dotenv()
    agent = HelloAgent()
    print(agent.get_response_text("Hello"))
