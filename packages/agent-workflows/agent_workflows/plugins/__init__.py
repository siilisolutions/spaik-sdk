"""Agent Workflows Plugin system"""

import importlib
from typing import Any, Dict, Protocol, Awaitable, cast


class PluginModule(Protocol):
    def execute(self, ctx: Dict[str, Any]) -> Awaitable[None]:
        ...


async def load_plugin(plugin_path: str, ctx: Dict[str, Any]) -> None:
    """Load and execute a plugin"""
    # Parse plugin path: namespace/name@version
    plugin_name = plugin_path.split('@')[0]  # ignore version for now

    # Convert to module path
    module_path = f"agent_workflows.plugins.{plugin_name.replace('/', '.')}"

    try:
        module = importlib.import_module(module_path)
        plugin = cast(PluginModule, module)
        await plugin.execute(ctx)
    except ImportError:
        raise Exception(f"Plugin not found: {plugin_path}")