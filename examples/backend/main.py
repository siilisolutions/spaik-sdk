from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from siili_agent_sdk import BaseAgent, LLMConfig, ProviderType, LLMModel

app = FastAPI(title="Agent SDK Backend", version="0.1.0")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


class SimpleAgent(BaseAgent):
    def __init__(self):
        config = LLMConfig(
            provider=ProviderType.OPENAI_DIRECT,
            model=LLMModel.O3_MINI_LATEST,
            temperature=0.7,
        )
        super().__init__(config)
    
    async def process_message(self, message: str) -> str:
        # TODO: Implement actual agent logic
        return f"Agent response to: {message}"


# Global agent instance
agent = SimpleAgent()


@app.get("/")
async def health_check():
    return {"status": "healthy", "service": "agent-backend"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response = await agent.process_message(request.message)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 