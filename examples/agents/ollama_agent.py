"""Runs an agent with tools on a local Ollama model.

Start Ollama with `ollama serve`, pull the model with `ollama pull gpt-oss:20b`, and set
OLLAMA_BASE_URL if the server is not at http://localhost:11434.
"""

from dotenv import load_dotenv
from spaik_sdk import BaseAgent, LLMModel
from spaik_sdk.tools.tool_provider import tool


@tool
def monthly_loan_payment(principal: float, annual_interest_rate_percent: float, years: int) -> str:
    """Calculate the fixed monthly payment of an amortising loan.

    Args:
        principal: Amount borrowed.
        annual_interest_rate_percent: Nominal yearly interest rate, e.g. 4.5 for 4.5 %.
        years: Loan term in years.
    """
    months = years * 12
    monthly_rate = annual_interest_rate_percent / 100 / 12
    if monthly_rate == 0:
        payment = principal / months
    else:
        payment = principal * monthly_rate / (1 - (1 + monthly_rate) ** -months)
    return f"Monthly payment: {payment:.2f}. Total repaid: {payment * months:.2f}."


class LoanAdvisorAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            system_prompt="You help people understand loan costs. Use the monthly_loan_payment tool for every calculation.",
            llm_model=LLMModel(family="ollama", name="gpt-oss:20b", reasoning=True, prompt_caching=False),
            tools=[monthly_loan_payment],
        )


if __name__ == "__main__":
    load_dotenv()
    agent = LoanAdvisorAgent()
    question = "I want to borrow 250,000 at 4.2 % for 25 years. What would I pay each month, and how much interest in total?"
    print(agent.get_response_text(question))
