import os
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from retrieval_engine import query_documents
from query_logger import log_query
import time

llm = LLM(
    model="ollama_chat/gpt-oss:20b",
    base_url="https://ollama.com",
    api_key=os.getenv("OLLAMA_API_KEY"),
)


@tool("RAG Retrieval Tool")
def rag_tool(question: str, department: str = None) -> str:
    """Retrieve raw source excerpts for a question, optionally scoped to a department (HR, Finance, Legal, Customer). Returns only retrieved text, no pre-synthesized answer."""
    result = query_documents(question, department)
    chunks_text = chr(10).join([f"[Source: {c['file_name']}, relevance: {c['score']}] {c['text']}" for c in result['raw_chunks']])
    return f"Raw Source Excerpts:\n{chunks_text}\n\nDepartment: {result['department']}"


router_agent = Agent(
    role="Query Router",
    goal="Determine which department (HR, Finance, Legal, Customer) a user question relates to",
    backstory="Expert at classifying organizational questions into the correct department.",
    llm=llm,
    verbose=True,
)

retrieval_agent = Agent(
    role="Retrieval Specialist",
    goal="Retrieve relevant document chunks and answers using the RAG tool. Call the tool exactly once per question. If the retrieved source excerpts do not contain information that answers the question, state plainly that the information was not found in the available documents. Never invent, assume, or fabricate details, numbers, or procedures that are not explicitly present in the raw source excerpts.",
    backstory="A disciplined researcher who only reports what is explicitly written in the source documents, and clearly says when information is missing rather than guessing.",
    tools=[rag_tool],
    llm=llm,
    verbose=True,
)

verification_agent = Agent(
    role="Verification Officer",
    goal="Check that the retrieved answer is actually supported by the source documents",
    backstory="Meticulous reviewer who flags weak or unsupported answers, and confirms clearly worded 'not found' answers as accurate when the source genuinely lacks the information.",
    llm=llm,
    verbose=True,
)

response_agent = Agent(
    role="Response Formatter",
    goal="Produce a final, clear, direct answer for the end user, with source citations. Always output a complete final answer to the user's original question — never ask the user for more information, never critique the prior agents' work, never request source excerpts from the user. If the documents did not contain the answer, say so in one or two plain sentences and stop there.",
    backstory="A skilled communicator who writes clean, final, user-facing answers exactly as a helpful human assistant would — direct, concise, and always resolving the conversation rather than deferring it back to the user.",
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
        description=f"Using the RAG Retrieval Tool, answer this question: '{question}'. Use the department identified by the previous task. Call the tool only once. If the source excerpts do not answer the question, clearly state that the information was not found.",
        expected_output="An answer with sources, or a clear statement that the information was not found in the available documents.",
        agent=retrieval_agent,
        context=[route_task],
    )

    verify_task = Task(
        description="You have been given the Retrieval Specialist's answer and source excerpts in your context. Read that context carefully before responding. Verify the retrieved answer is supported by its cited sources. If the answer states information was not found, confirm whether the source excerpts genuinely lack that information. If for any reason no prior answer appears in your context, treat this as a system error and respond with exactly: SYSTEM_ERROR_NO_CONTEXT -- do not claim the source lacks information in this case.",
        expected_output="A verified answer with a confidence note, or the literal string SYSTEM_ERROR_NO_CONTEXT if no context was received.",
        agent=verification_agent,
        context=[retrieve_task],
    )

    respond_task = Task(
        description=f"Write the final, user-facing answer to the original question: '{question}'. Include source citations where the answer was found in the documents. This is the final answer shown to the user — do not ask for more information, do not critique prior steps, just answer. If your context contains the literal string SYSTEM_ERROR_NO_CONTEXT, ignore it and instead base your answer directly on the Retrieval Specialist's original answer, which is also available to you in the full task history.",
        expected_output="A complete, final, direct answer to the user's question, ready to be shown as-is.",
        agent=response_agent,
        context=[retrieve_task, verify_task],
    )

    crew = Crew(
        agents=[router_agent, retrieval_agent, verification_agent, response_agent],
        tasks=[route_task, retrieve_task, verify_task, respond_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()
    department = route_task.output.raw.strip() if route_task.output else "unknown"
    return result, department


def run_query_logged(question: str):
    """Wraps run_query with timing and logging to query_logs."""
    start = time.time()
    result, department = run_query(question)
    duration = time.time() - start
    log_query(
        question=question,
        department=department,
        answer=str(result),
        duration_s=duration,
    )
    return result


if __name__ == "__main__":
    result = run_query_logged("What is the leave policy?")
    print("\n\n=== FINAL RESULT ===")
    print(result)
