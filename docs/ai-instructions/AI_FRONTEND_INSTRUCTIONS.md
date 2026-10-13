# Frontend integration instructions

Use official AG-UI AbstractAgent/HttpAgent state, scoped AgentSdkClientProvider, optional ThreadRepository and the shared Material kit. Do not implement custom event parsing or duplicate message/block renderers. Message is the AG-UI type; use messageText. Preserve reasoning, tools, state, attachments/audio and renderer overrides.

The maintained API reference and examples are in [the package README](../../packages/agent-sdk-hooks/README.md). See [migration guidance](../MIGRATING_TO_1_0.md) and [release gates](../SPAIK_1_0_PLAN.md). This replaces the obsolete block-protocol instructions.
