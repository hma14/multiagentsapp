from fastapi import FastAPI, Depends
from sqlmodel import Session, select
from db.models import PromptResult, SQLModel
from db.session import engine, get_session
from agents.agent_manager import run_agents
from fastapi.middleware.cors import CORSMiddleware
from agents.ai_agents.ai_agent_search import run_chatbot

app = FastAPI()

# Allow frontend (localhost:3000) to talk to backend (localhost:8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # or ["*"] for all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create DB tables on startup
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.post("/api/query")
def query_agents(prompt: str, session: Session = Depends(get_session)):
    results =  run_chatbot(prompt) 
    #results =  run_agents(prompt)  # multi-agent logic
    if results is None:
        return results
    record = PromptResult(prompt=prompt, results=results)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

@app.get("/api/results")
def get_results(session: Session = Depends(get_session)):
    results = session.exec(select(PromptResult)).all()
    return [r.model_dump() for r in results]

