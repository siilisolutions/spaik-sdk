# Server integration instructions

Use ApiBuilder and a repository/authorizer. Thread ownership starts at creation. /threads/{id}/runs accepts RunAgentInput and streams official AG-UI SSE. History is authoritative; reject edits/conflicting IDs/overlapping runs and persist checkpoints/partial output. The local runner supports one process per repository. Files/audio routes remain optional. SignalR, Azure queue helpers and streaming negotiation have been removed.

The maintained API reference and examples are in [the package README](../../packages/agent-sdk/README.md). See [migration guidance](../MIGRATING_TO_1_0.md) and [release gates](../SPAIK_1_0_PLAN.md). This replaces the obsolete block-protocol instructions.
