# Python agent instructions

Use arbitrary IDs with explicit providers or inject BaseChatModel. Response methods return AG-UI assistant messages; streaming methods yield official AG-UI events. Keep private provider replay metadata and tool-history controls. Prices are never inferred; get_cost reads recorded charges.

The maintained API reference and examples are in [the package README](../../packages/agent-sdk/README.md). See [migration guidance](../MIGRATING_TO_1_0.md) and [release gates](../SPAIK_1_0_PLAN.md). This replaces the obsolete block-protocol instructions.
