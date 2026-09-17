import os
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from retrieval_engine import query_documents

llm = LLM(
    model="ollama_chat/gpt-oss:20b",
    base_url="https://ollama.com",
    api_key=os.getenv("OLLAMA_API_KEY"),
)


@tool("RAG Retrieval Tool")
def rag_tool(question: str, department: str = None) -> str:
    """Retrieve an answer and sources for a question, optionally scoped to a department (HR, Finance, Legal, Customer)."""
    result = query_documents(question, department)
    chunks_text = chr(10).join([f"[Source: {c['file_name']}, relevance: {c['score']}] {c['text']}" for c in result['raw_chunks']])
    return f"Answer: {result['answer']}\n\nRaw Source Excerpts:\n{chunks_text}\n\nDepartment: {result['department']}"


router_agent = Agent(
    role="Query Router",
    goal="Determine which department (HR, Finance, Legal, Customer) a user question relates to",
    backstory="Expert at classifying organizational questions into the correct department.",
    llm=llm,
    verbose=True,
)

retrieval_agent = Agent(
    role="Retrieval Specialist",
    goal="Retrieve relevant document chunks and answers using the RAG tool",
    backstory="Specialist in fetching accurate information from the document knowledge base.",
    tools=[rag_tool],
    llm=llm,
    verbose=True,
)

verification_agent = Agent(
    role="Verification Officer",
    goal="Check that the retrieved answer is actually supported by the source documents",
    backstory="Meticulous reviewer who flags weak or unsupported answers.",
    llm=llm,
    verbose=True,
)

response_agent = Agent(
    role="Response Formatter",
    goal="Produce a final, clear answer with proper source citations",
    backstory="Skilled communicator who writes clean, cited answers for business users.",
    llm=llm,
    verbose=True,
)


def run_query(question: str):
    route_task = Task(
        description=f"Classify this question into one department (HR, Finance, Legal, Customer): '{question}'. Respond with only the department name.",
        expected_output="A single department name.",
        agent=router_agent,
    )

    retrieve_task = Task(
        description=f"Using the RAG Retrieval Tool, answer this question: '{question}'. Use the department identified by the previous task.",
        expected_output="An answer with sources.",
        agent=retrieval_agent,
        context=[route_task],
    )

    verify_task = Task(
        description="Verify the retrieved answer is supported by its cited sources. Note any concerns.",
        expected_output="A verified answer with a confidence note.",
        agent=verification_agent,
        context=[retrieve_task],
    )

    respond_task = Task(
        description="Write the final answer clearly, with source citations included.",
        expected_output="Final formatted answer with citations.",
        agent=response_agent,
        context=[verify_task],
    )

    crew = Crew(
        agents=[router_agent, retrieval_agent, verification_agent, response_agent],
        tasks=[route_task, retrieve_task, verify_task, respond_task],
        process=Process.sequential,
        verbose=True,
    )

    return crew.kickoff()


if __name__ == "__main__":
    result = run_query("What is the leave policy?")
    print("\n\n=== FINAL RESULT ===")
    print(result)
