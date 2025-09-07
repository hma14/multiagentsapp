from fastapi import FastAPI, Depends
from sqlmodel import Session, select
from db.models import PromptResult, SQLModel
from db.session import engine, get_session
from agents.agent_manager import run_agents
from fastapi.middleware.cors import CORSMiddleware
from agents.ai_agents.ai_agent_search import run_chatbot
from contextlib import asynccontextmanager

app = FastAPI()

# Allow frontend (localhost:3000) to talk to backend (localhost:8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["*"] for all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create DB tables on startup    
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    SQLModel.metadata.create_all(engine)
    print("Database tables created")
    yield
    # Optional shutdown code
    print("App shutting down")

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
def get_results(session: Session = Depends(get_session), page: int = 1, page_size: int = 10):
    offset = (page - 1) * page_size
    
    statement = (
        select(PromptResult)
        .order_by(PromptResult.createdAt.desc())
        .offset(offset)
        .limit(page_size)
    )
    results = session.exec(statement).all()
    
    # total count query
    from sqlalchemy import func
    total = session.exec(select(func.count()).select_from(PromptResult)).one()

    return {
        "results": [r.model_dump() for r in results],
        "total": total,
    }

