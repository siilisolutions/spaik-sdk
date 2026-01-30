from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from spaik_sdk.audio import AudioFormat, SpeechToText, STTOptions, TextToSpeech, TTSOptions
from spaik_sdk.server.authorization.base_authorizer import BaseAuthorizer
from spaik_sdk.server.authorization.base_user import BaseUser
from spaik_sdk.utils.init_logger import init_logger

logger = init_logger(__name__)


class TTSRequest(BaseModel):
    """Request body for text-to-speech synthesis."""

    text: str
    model: Optional[str] = None
    voice: str = "alloy"
    speed: float = 1.0
    format: str = "mp3"


class STTResponse(BaseModel):
    """Response from speech-to-text transcription."""

    text: str


class AudioRouterFactory:
    """Factory for creating audio API routes (TTS/STT)."""

    def __init__(
        self,
        authorizer: Optional[BaseAuthorizer[BaseUser]] = None,
        tts_model: Optional[str] = None,
        stt_model: Optional[str] = None,
    ):
        self.authorizer = authorizer
        self.tts_model = tts_model
        self.stt_model = stt_model

    def create_router(self, prefix: str = "/audio") -> APIRouter:
        router = APIRouter(prefix=prefix, tags=["audio"])

        async def get_current_user(request: Request) -> BaseUser:
            if self.authorizer is None:
                return BaseUser("anonymous")
            user = await self.authorizer.get_user(request)
            if not user:
                raise HTTPException(status_code=401, detail="Unauthorized")
            return user

        @router.post("/speech")
        async def text_to_speech(
            request: TTSRequest,
            user: BaseUser = Depends(get_current_user),
        ):
            """
            Convert text to speech audio.

            Returns audio bytes in the specified format (default: mp3).
            """
            try:
                # Map format string to enum
                format_map = {
                    "mp3": AudioFormat.MP3,
                    "opus": AudioFormat.OPUS,
                    "aac": AudioFormat.AAC,
                    "flac": AudioFormat.FLAC,
                    "wav": AudioFormat.WAV,
                    "pcm": AudioFormat.PCM,
                }
                output_format = format_map.get(request.format.lower(), AudioFormat.MP3)

                options = TTSOptions(
                    voice=request.voice,
                    speed=request.speed,
                    output_format=output_format,
                )

                tts = TextToSpeech(model=request.model or self.tts_model)
                audio_bytes = await tts.synthesize(text=request.text, options=options)

                # Determine content type
                content_type_map = {
                    AudioFormat.MP3: "audio/mpeg",
                    AudioFormat.OPUS: "audio/opus",
                    AudioFormat.AAC: "audio/aac",
                    AudioFormat.FLAC: "audio/flac",
                    AudioFormat.WAV: "audio/wav",
                    AudioFormat.PCM: "audio/pcm",
                }
                content_type = content_type_map.get(output_format, "audio/mpeg")

                return Response(
                    content=audio_bytes,
                    media_type=content_type,
                    headers={
                        "Content-Disposition": f'inline; filename="speech.{request.format}"',
                    },
                )
            except Exception as e:
                logger.error(f"TTS error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @router.post("/speech/stream")
        async def text_to_speech_stream(
            request: TTSRequest,
            user: BaseUser = Depends(get_current_user),
        ):
            """
            Stream text to speech audio.

            Streams audio chunks as they are generated, allowing playback to start immediately.
            This is faster for the user as audio begins playing before full generation is complete.
            """
            try:
                # Map format string to enum
                format_map = {
                    "mp3": AudioFormat.MP3,
                    "opus": AudioFormat.OPUS,
                    "aac": AudioFormat.AAC,
                    "flac": AudioFormat.FLAC,
                    "wav": AudioFormat.WAV,
                    "pcm": AudioFormat.PCM,
                }
                output_format = format_map.get(request.format.lower(), AudioFormat.MP3)

                options = TTSOptions(
                    voice=request.voice,
                    speed=request.speed,
                    output_format=output_format,
                )

                tts = TextToSpeech(model=request.model or self.tts_model)

                # Determine content type
                content_type_map = {
                    AudioFormat.MP3: "audio/mpeg",
                    AudioFormat.OPUS: "audio/opus",
                    AudioFormat.AAC: "audio/aac",
                    AudioFormat.FLAC: "audio/flac",
                    AudioFormat.WAV: "audio/wav",
                    AudioFormat.PCM: "audio/pcm",
                }
                content_type = content_type_map.get(output_format, "audio/mpeg")

                async def generate():
                    async for chunk in tts.synthesize_stream(text=request.text, options=options):
                        yield chunk

                return StreamingResponse(
                    generate(),
                    media_type=content_type,
                    headers={
                        "Content-Disposition": f'inline; filename="speech.{request.format}"',
                        "Cache-Control": "no-cache",
                    },
                )
            except Exception as e:
                logger.error(f"TTS stream error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @router.post("/transcribe", response_model=STTResponse)
        async def speech_to_text(
            file: UploadFile = File(...),
            language: Optional[str] = Form(None),
            prompt: Optional[str] = Form(None),
            user: BaseUser = Depends(get_current_user),
        ):
            """
            Transcribe audio file to text using OpenAI Whisper.

            Accepts audio files in various formats (webm, mp3, wav, m4a, ogg).
            """
            try:
                audio_bytes = await file.read()
                filename = file.filename or "audio.webm"

                logger.info(f"STT request: language={language}, filename={filename}, size={len(audio_bytes)}")

                options = STTOptions(
                    language=language,
                    prompt=prompt,
                )

                stt = SpeechToText(model=self.stt_model)
                text = await stt.transcribe(
                    audio_bytes=audio_bytes,
                    options=options,
                    filename=filename,
                )

                return STTResponse(text=text)
            except Exception as e:
                logger.error(f"STT error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        return router
