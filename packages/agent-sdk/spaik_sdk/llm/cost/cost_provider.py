import asyncio
import logging
from typing import Any
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel

from spaik_sdk.llm.cost.cost_estimate import CostEstimate

logger = logging.getLogger(__name__)


class CostContext(BaseModel):
    provider: str
    response_id: str | None = None
    metadata: dict[str, Any] = {}


class CostProvider:
    """Resolve charges once per invocation using the provider's convention.

    Extra requests are supported only for recognized request-level billing APIs.
    API keys remain on this resolver, never in persisted context.
    """

    def __init__(self, provider: str = "", base_url: str = "", api_key: str | None = None):
        self.provider = provider
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._cache: dict[str, CostEstimate | None] = {}
        self._pending: dict[str, asyncio.Task[CostEstimate | None]] = {}
        self._warned = False

    async def resolve(self, context: CostContext) -> CostEstimate | None:
        key = context.response_id
        if key and key in self._cache:
            return self._cache[key]
        if key and key in self._pending:
            return await asyncio.shield(self._pending[key])
        task = asyncio.create_task(self._resolve(context))
        if key:
            self._pending[key] = task

            def complete(done: asyncio.Task[CostEstimate | None]) -> None:
                self._pending.pop(key, None)
                if not done.cancelled():
                    self._cache[key] = done.result()

            task.add_done_callback(complete)
        return await asyncio.shield(task)

    async def _resolve(self, context: CostContext) -> CostEstimate | None:
        metadata = context.metadata
        usage = metadata.get("usage") or metadata.get("token_usage") or {}
        try:
            # A named cost field with an explicit currency is accepted for custom providers.
            charge = metadata.get("cost")
            currency = metadata.get("currency")
            openrouter = context.provider == "openrouter" or urlparse(self.base_url).hostname == "openrouter.ai"
            if openrouter:
                charge = usage.get("cost", charge)
                currency = currency or "USD"
            if charge is not None and currency:
                return CostEstimate(cost=charge, currency=currency)
            if openrouter and context.response_id and self.api_key:
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get(
                        "https://openrouter.ai/api/v1/generation",
                        params={"id": context.response_id},
                        headers={"Authorization": f"Bearer {self.api_key}"},
                    )
                    response.raise_for_status()
                    charge = response.json()["data"].get("total_cost")
                    if charge is not None:
                        return CostEstimate(cost=charge, currency="USD")
        except Exception:
            # Billing is ancillary: do not expose credentials or fail inference.
            logger.debug("Request-level cost resolution failed")
        if not self._warned:
            logger.warning("Cost unavailable: this provider does not expose a request-level charge.")
            self._warned = True
        return None
