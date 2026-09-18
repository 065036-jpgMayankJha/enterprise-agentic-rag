import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from crew_agents import run_query
from retrieval_engine import query_documents

app = FastAPI(title="Enterprise RAG API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    department: str
    sources: list[str] = []


@app.get("/")
def root():
    return {"status": "ok", "message": "Enterprise RAG API is running"}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    result, department = run_query(request.question)
    answer_text = str(result)

    dept_for_lookup = department if department != "unknown" else None
    retrieval_result = query_documents(request.question, dept_for_lookup)
    sources = retrieval_result["sources"]

    return QueryResponse(
        answer=answer_text,
        department=department,
        sources=sources,
    )
