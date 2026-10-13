# Spaik AG-UI backend

This example/template supplies FastAPI thread management and AG-UI runs, files and audio using `ApiBuilder.local`. Configure `DEFAULT_MODEL` (a preset alias or API ID), `MODEL_PROVIDER`, and the provider API key in your environment. For arbitrary model IDs use an explicit provider.

Run `uv sync` then `uv run uvicorn main:app --reload`. The frontend uses http://localhost:8000. The local repository writes JSON to `data-v1`; use one server worker per repository.

Routes: thread CRUD under `/threads`, `POST /threads/{id}/runs` (official AG-UI RunAgentInput/SSE), `POST /threads/{id}/cancel`, `/files`, `/audio/speech`, `/audio/transcribe`. The legacy `/messages/stream`, Azure queue and SignalR transports are removed. See the repository's `docs/MIGRATING_TO_1_0.md` for persistence and client migration.

Provider, audio, MCP and server dependencies are optional extras in the SDK; trim this example's extras to match your application. Application-owned tools require no built-in search service or extra search key.
