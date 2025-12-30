import os

from siili_coding_agents import CursorAgent, CursorAgentOptions


def main() -> None:
    # Cursor agent - verifies connection automatically on init
    options = CursorAgentOptions(
        output_format="stream-json",
        working_directory=os.getcwd(),
        yolo=True,
        # verify_on_init=True,  # default
        # verify_timeout=30.0,  # default
    )
    
    # This will raise AgentConnectionError if not authenticated
    agent = CursorAgent(options)
    
    # Run tasks
    agent.run("write a joke about cats in cat_joke.md")


if __name__ == "__main__":
    main()
