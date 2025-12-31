"""Agent Workflows Plugin system"""

import importlib
from typing import Any, Awaitable, Dict, Protocol, Union, cast


class PluginModule(Protocol):
    def execute(self, ctx: Dict[str, Any]) -> Awaitable[Union[Dict[str, Any], None]]:
        ...


async def load_plugin(plugin_path: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Load and execute a plugin.

    Args:
        plugin_path: Plugin path like 'namespace/name' or 'namespace/name@version'
        ctx: Execution context with 'with', 'env', 'workspace', 'logger', etc.

    Returns:
        Dict of output values from the plugin, or empty dict if plugin returns None.
    """
    # Parse plugin path: namespace/name@version
    plugin_name = plugin_path.split("@")[0]  # ignore version for now

    # Convert to module path
    module_path = f"agent_workflows.plugins.{plugin_name.replace('/', '.')}"

    try:
        module = importlib.import_module(module_path)
        plugin = cast(PluginModule, module)
        result = await plugin.execute(ctx)
        return result if isinstance(result, dict) else {}
    except ImportError as e:
        raise Exception(f"Plugin not found: {plugin_path} ({e})")
