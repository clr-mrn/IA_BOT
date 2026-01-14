from fastapi import FastAPI
from pydantic import BaseModel, Field
from backend.services.agent import Agent
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI(title="IA Bot Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = Agent()

class ChatRequest(BaseModel):
    conversation_id: str = Field(default="default")
    message: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]
    trace: dict

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    result = await agent.run(conversation_id=req.conversation_id, user_message=req.message)
    return result
