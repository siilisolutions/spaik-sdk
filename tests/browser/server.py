"""Deterministic backend and independent AG-UI endpoint for browser/contract tests."""
import asyncio
import io
import wave

from ag_ui import core as ui
from ag_ui.encoder import EventEncoder
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from spaik_sdk import BaseAgent
from spaik_sdk.server.api.routers.api_builder import ApiBuilder

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173'], allow_methods=['*'], allow_headers=['*'])
agent = BaseAgent(system_prompt='test', chat_model=FakeListChatModel(responses=['Hello from Spaik. ' * 5], sleep=0.02))
builder = ApiBuilder.local(agent=agent, in_memory=True)
app.include_router(builder.build_thread_router())
app.include_router(builder.build_file_router())


@app.post('/audio/speech')
async def speech():
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b'\x00\x00' * 800)
    return Response(buffer.getvalue(), media_type='audio/wav')


@app.post('/audio/transcribe')
async def transcribe():
    return {'text': 'Transcribed test audio'}


@app.post('/external')
async def external(body: dict):
    async def events():
        encoder = EventEncoder()
        sequence = [
            ui.RunStartedEvent(thread_id=body['threadId'], run_id=body['runId']),
            ui.StateSnapshotEvent(snapshot={'progress': 'done'}),
            ui.ReasoningStartEvent(message_id='reasoning'), ui.ReasoningMessageStartEvent(message_id='reasoning'),
            ui.ReasoningMessageContentEvent(message_id='reasoning', delta='External reasoning summary'),
            ui.ReasoningMessageEndEvent(message_id='reasoning'), ui.ReasoningEndEvent(message_id='reasoning'),
            ui.TextMessageStartEvent(message_id='external-answer', role='assistant'),
            ui.TextMessageContentEvent(message_id='external-answer', delta='Independent AG-UI response'),
            ui.ToolCallStartEvent(tool_call_id='external-tool', tool_call_name='weather', parent_message_id='external-answer'),
            ui.ToolCallArgsEvent(tool_call_id='external-tool', delta='{"city":"Helsinki"}'),
            ui.ToolCallEndEvent(tool_call_id='external-tool'),
            ui.ToolCallResultEvent(tool_call_id='external-tool', message_id='external-result', content='sunny', role='tool'),
            ui.TextMessageEndEvent(message_id='external-answer'),
            ui.RunFinishedEvent(thread_id=body['threadId'], run_id=body['runId']),
        ]
        for event in sequence:
            yield encoder.encode(event)
            await asyncio.sleep(0.005)
    return StreamingResponse(events(), media_type='text/event-stream')
