"""API FastAPI : expose l'agent pour que n'importe quelle application puisse l'interroger.

Lancement :
    uvicorn src.api:app --reload
Documentation interactive :
    http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from src.agent import agent
from src.config import text_of

app = FastAPI(
    title="Olist Copilot",
    description="Agent IA qui répond à des questions business sur les données e-commerce Olist.",
    version="1.0",
)


# --- Le format des données échangées -----------------------------------------
class Question(BaseModel):
    question: str


class Answer(BaseModel):
    question: str
    answer: str
    tools_used: list[str]


# --- Les endpoints -------------------------------------------------------------
@app.get("/health")
def health():
    """Vérifie que le service est en ligne."""
    return {"status": "ok"}


@app.post("/ask", response_model=Answer)
def ask(q: Question):
    """Pose une question à l'agent et renvoie sa réponse, avec les outils utilisés."""
    result = agent.invoke(
        {"messages": [HumanMessage(content=q.question)]},
        config={"recursion_limit": 15},
    )
    # On liste les outils appelés par l'agent, pour la transparence
    tools_used = [
        call["name"]
        for msg in result["messages"]
        for call in (getattr(msg, "tool_calls", None) or [])
    ]
    return Answer(
        question=q.question,
        answer=text_of(result["messages"][-1]),
        tools_used=tools_used,
    )