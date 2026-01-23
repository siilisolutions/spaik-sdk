import os

from spaik_coding_agents import CursorAgent, CursorAgentOptions


def main() -> None:
    # Cursor agent - verifies connection automatically on init
    options = CursorAgentOptions(
        output_format="stream-json",
        working_directory=os.getcwd(),
        yolo=True,
    )
    
    # This will raise AgentConnectionError if not authenticated
    agent = CursorAgent(options)
    
    # Run task and get result
    result = agent.run("write a joke about cats in cat_joke.md")
    print(f"\n=== Result ===\n{result}")


if __name__ == "__main__":
    main()
