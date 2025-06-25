from siili_ai_sdk.agent.base_agent import BaseAgent
from siili_ai_sdk.thread.adapters.cli.live_cli import LiveCLI
from siili_ai_sdk.thread.adapters.sync_adapter import SyncAdapter


class MinimalAgent(BaseAgent):
    async def run(self, input: str) -> None:
        cli = LiveCLI(self.thread_container)
        await cli.run(self.get_response_stream(input))
        self.thread_container.print_all()

    async def run_interactive(self) -> None:
        cli = LiveCLI(self.thread_container)
        await cli.run_interactive(self)
        for event in cli.events:
            print(event)
        self.thread_container.print_all()

    def run_sync(self, input: str) -> None:
        response = SyncAdapter(self.thread_container).run(self.get_response_stream(input)).get_final_response()
        print(response)
        self.thread_container.print_all()
