# Spaik AG-UI backend

A FastAPI server that exposes a Spaik agent over AG-UI, with thread management, file uploads and audio, using `ApiBuilder.local`. The agent has one example tool, `current_time`; replace it with your own.

Configure `DEFAULT_MODEL` (a preset alias or model ID), `MODEL_PROVIDER` and the provider API key in `.env`. Arbitrary model IDs need an explicit provider.

Run `uv sync`, then `uv run uvicorn main:app --reload`. The server listens on http://localhost:8000 and accepts requests from the frontend at http://localhost:5173. Local storage writes JSON to `data-v1`; run one server worker per repository.

Routes: thread CRUD under `/threads`, `POST /threads/{id}/runs` (official AG-UI `RunAgentInput`, streamed as SSE), `POST /threads/{id}/cancel`, `/files`, `/audio/speech` and `/audio/transcribe`. The legacy `/messages/stream`, Azure queue and SignalR transports were removed in 1.0; see the repository's `docs/MIGRATING_TO_1_0.md`.

Provider, audio, MCP and server support are optional SDK extras. Trim the extras in `pyproject.toml` to the ones your application uses.
