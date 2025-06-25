from typing import Any

from siili_ai_sdk.server.queue.agent_job_queue import AgentJob
from siili_ai_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


class AzureFunctionQueue:
    """Azure Functions queue implementation"""

    def __init__(self, func_out: Any):
        """
        Args:
            func_out: Azure Functions queue output binding (func.Out[str])
        """
        self.func_out = func_out

    async def push(self, job: AgentJob) -> None:
        """Push job to Azure Functions queue"""
        json_data = job.to_json()

        # Set the message in the Azure Functions queue output
        self.func_out.set(json_data)
