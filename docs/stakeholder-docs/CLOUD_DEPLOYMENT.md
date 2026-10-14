# Cloud deployment

Deploy the React/Material frontend as static assets and the Python FastAPI backend as a long-running service on your preferred cloud. AG-UI runs use HTTP POST plus `text/event-stream`; configure the reverse proxy to disable buffering, allow long-lived responses, forward authorization headers, and propagate disconnects.

Use one backend process per repository with the built-in runner. Local JSON storage is a development implementation. Production multi-worker deployments require application-owned durable repositories and distributed run/cancellation coordination; the SDK does not provide an Azure Functions queue or SignalR deployment adapter.

Azure OpenAI and Foundry model endpoints remain supported through optional model integrations. Cloud choice does not dictate model choice. Applications own identity/authorization hooks, secrets, durable storage and deployment infrastructure.

Validate thread ownership, cancellation/disconnect persistence, proxy streaming and installed-package compatibility in staging before release. Preserve the old storage and legacy application tag for rollback.
