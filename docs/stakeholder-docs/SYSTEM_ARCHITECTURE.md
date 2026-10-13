# Spaik 1.0 system architecture

Spaik focuses on thread management and a reusable UI kit with a small agent convenience layer.

```mermaid
flowchart LR
  UI[Material UI kit] --> Client[Official AG-UI client]
  Client --> Run[AG-UI run endpoint]
  UI --> Threads[Optional thread repository client]
  Threads --> API[Authorized thread CRUD]
  Run --> Agent[BaseAgent / LangChain]
  Run --> Store[Canonical AG-UI JSON envelope]
  API --> Store
  Agent --> Model[Injected model or provider/model ID]
  Agent --> Tools[Application-owned tools]
  Agent --> Usage[Reported token usage and optional charges]
```

The UI also connects directly to independent AG-UI backends. Thread listing/storage is optional for those integrations. Official message and event types replace the custom block protocol. Private provider replay/signature data stays outside public thread responses. Recording and tracing remain available.

The local runner coordinates one server process per repository. Applications supply distributed storage/run coordination for multi-worker deployments. File uploads and speech are separate optional routes. Provider SDKs are optional; the preset catalog is never an eligibility requirement. No price table or organization-billing allocation is maintained.

See [migration guidance](../MIGRATING_TO_1_0.md) and [release gates](../SPAIK_1_0_PLAN.md).
