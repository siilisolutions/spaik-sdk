import os

from siili_coding_agents import ClaudeAgent, CursorAgent, CursorAgentOptions


def main() -> None:
    # Claude Code agent (commented out)
    # from siili_coding_agents import ClaudeAgentOptions
    # agent = ClaudeAgent(ClaudeAgentOptions(yolo=True))
    # agent.run("search online for latest news, then write them as news.md")
    
    # Cursor CLI agent with session management
    options = CursorAgentOptions(
        api_key=os.getenv("CURSOR_API_KEY"),
        output_format="stream-json",  # Use stream-json for better real-time output
        working_directory=os.getcwd(),
        yolo=True,
    )
    
    agent = CursorAgent(options)
    
    # These calls will use the same session (stored in memory during agent lifetime)
    # If no session exists, it will create one automatically
    agent.run("write a joke about cats in cat_joke.md")
    agent.run("make it much spicier")
    
    # Optional: Clear session from memory
    # agent.clear_session()
    
    # Note: Sessions are only maintained in memory during the agent's lifetime
    # New agent instances will create fresh sessions

if __name__ == "__main__":
    main()
