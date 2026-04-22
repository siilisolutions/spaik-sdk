from unittest.mock import MagicMock, patch

import pytest
from langchain_core.tools import tool

from spaik_sdk.llm.langchain_service import LangChainService


@pytest.mark.unit
class TestCreateExecutorToolErrorHandling:
    def test_wraps_tools_in_tool_node_with_error_handling(self):
        # Regression test for issue #61: the LangGraph default tool error
        # handler re-raises any runtime tool exception, killing the agent
        # loop. We now wrap tools in a ToolNode with handle_tool_errors=True
        # so errors become ToolMessage errors the LLM can react to.
        @tool
        def sample_tool(x: int) -> int:
            """Sample tool."""
            return x

        service = LangChainService(
            llm_config=MagicMock(),
            thread_container=MagicMock(thread_id="t"),
            assistant_name="a",
            assistant_id="a",
        )

        fake_model = object()
        with patch.object(LangChainService, "_get_model", return_value=fake_model):
            with patch("spaik_sdk.llm.langchain_service.create_react_agent") as mock_create:
                with patch("spaik_sdk.llm.langchain_service.ToolNode") as mock_tool_node:
                    mock_tool_node.return_value = "tool-node-sentinel"
                    service.create_executor([sample_tool])

        mock_tool_node.assert_called_once_with([sample_tool], handle_tool_errors=True)
        mock_create.assert_called_once_with(fake_model, "tool-node-sentinel")
