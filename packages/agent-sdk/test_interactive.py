#!/usr/bin/env python3

import asyncio

from siili_ai_sdk.demo_agents.demo_agent import DemoAgent


async def main():
    agent = DemoAgent()
    await agent.run_interactive()


if __name__ == "__main__":
    asyncio.run(main())
