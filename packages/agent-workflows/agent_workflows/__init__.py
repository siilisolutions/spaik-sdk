"""Agent Workflows - YAML-driven workflow engine for AI agents"""

import warnings

__version__ = "0.3.2"

warnings.warn(
    "spaik-agent-workflows is deprecated and requires spaik-sdk==0.11.1 and "
    "spaik-coding-agents==0.2.3; it does not support Spaik 1.0.",
    FutureWarning,
    stacklevel=2,
)
