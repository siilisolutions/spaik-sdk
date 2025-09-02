from siili_coding_agents.claude_code.claude_agent import ClaudeAgent


def main() -> None:
    agent = ClaudeAgent(yolo=True)
    agent.run("search online for latest news, then write them as news.md")

if __name__ == "__main__":
    main() 