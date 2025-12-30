from typing import List

from dotenv import load_dotenv
from siili_ai_sdk.agent.base_agent import BaseAgent
from siili_ai_sdk.models.llm_model import LLMModel
from siili_ai_sdk.tools.tool_provider import BaseTool, ToolProvider, tool


@tool
def calculator(expression: str) -> str:
    """Evaluate mathematical expressions safely. Supports basic operations (+, -, *, /) and sqrt function.
    
    Args:
        expression: Mathematical expression to evaluate (e.g., '2+2', '10*5', 'sqrt(16)')
    """
    try:
        # Simple safe evaluation - only allow basic math operations
        if "sqrt" in expression:
            import math
            # Replace sqrt with math.sqrt
            expression = expression.replace("sqrt", "math.sqrt")
            result = eval(expression, {"__builtins__": {}, "math": math})
        else:
            # Basic arithmetic only
            allowed_chars = set("0123456789+-*/.() ")
            if not all(c in allowed_chars for c in expression):
                return f"Error: Invalid characters in expression '{expression}'. Only numbers and +, -, *, /, (, ) are allowed."
            
            result = eval(expression, {"__builtins__": {}})
        
        return f"Result: {result}"
    except Exception as e:
        return f"Error evaluating '{expression}': {str(e)}"


class CalculatorToolProvider(ToolProvider):
    def get_tools(self) -> List[BaseTool]:
        return [calculator]


class OllamaAgent(BaseAgent):
    """
    Sample agent demonstrating Ollama provider with gpt-oss:20b model.
    
    Features demonstrated:
    - Tool calling with a simple calculator tool
    - Reasoning mode (chain-of-thought)
    - Streaming responses
    
    Prerequisites:
    1. Install and start Ollama: `ollama serve`
    2. Download the model: `ollama pull gpt-oss:20b`
    3. Set OLLAMA_BASE_URL environment variable if not using default (http://localhost:11434)
    """
    
    def __init__(self):
        # Create Ollama model - users can create any Ollama model this way
        ollama_model = LLMModel(
            family="ollama",
            name="gpt-oss:20b",
            reasoning=True,  # This model supports reasoning
            prompt_caching=False  # Ollama doesn't support prompt caching like cloud providers
        )
        
        super().__init__(
            system_prompt="You are a helpful AI assistant with access to a calculator. "
                         "When asked to perform calculations, use the calculator tool. "
                         "Show your reasoning step by step for complex problems.",
            llm_model=ollama_model
        )

    def get_tool_providers(self) -> List[ToolProvider]:
        return [CalculatorToolProvider()]


if __name__ == "__main__":
    load_dotenv()
    
    print("🦙 Ollama Agent Demo")
    print("Prerequisites:")
    print("1. Start Ollama server: ollama serve")
    print("2. Download model: ollama pull gpt-oss:20b")
    print("3. Set OLLAMA_BASE_URL if not using localhost:11434")
    print()
    
    agent = OllamaAgent()
    
    # Test basic response
    print("=== Basic Response ===")
    response = agent.get_response_text("Hello! What can you help me with?")
    print(response)
    print()
    
    # Test tool calling
    print("=== Tool Calling Test ===")
    response = agent.get_response_text("What is 15 * 7 + 12?")
    print(response)
    print()
    
    # Test reasoning with complex math
    print("=== Reasoning + Tool Test ===")
    response = agent.get_response_text("I have a rectangle with length 12.5 and width 8.3. What's its area and perimeter?")
    print(response)
    print()
    
    # Interactive CLI (uncomment to use)
    # print("Starting interactive CLI...")
    # agent.run_cli()
