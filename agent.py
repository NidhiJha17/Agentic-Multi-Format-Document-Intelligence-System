from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq

from loader import load_cuad_txt_contracts
from chunker import chunk_contracts
from hybrid_retriever import HybridRetriever

llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0, max_tokens=8000, reasoning_effort="low")


class AgentState(TypedDict):
    query: str              # original user question, never changes
    search_query: str       # current search query, CAN change between retries
    retrieved_chunks: List[dict]
    attempts: int
    is_sufficient: bool
    final_answer: str


def retrieve_node(state: AgentState, retriever: HybridRetriever) -> AgentState:
    print(f"\n[RETRIEVE] Searching for: '{state['search_query']}' (attempt {state['attempts'] + 1})")
    results = retriever.search(state["search_query"], top_k=5)

    existing_ids = {c["chunk_id"] for c in state["retrieved_chunks"]}
    new_chunks = [r for r in results if r["chunk_id"] not in existing_ids]

    state["retrieved_chunks"].extend(new_chunks)
    state["attempts"] += 1
    print(f"[RETRIEVE] Got {len(new_chunks)} new chunks. Total so far: {len(state['retrieved_chunks'])}")
    return state


def reflect_node(state: AgentState) -> AgentState:
    print("[REFLECT] Checking if retrieved context is sufficient...")

    context = "\n\n".join(c["text"][:400] for c in state["retrieved_chunks"])

    prompt = f"""You are evaluating whether retrieved context is sufficient to answer a question.

Original question: {state['query']}

Retrieved context so far:
{context}

Respond in EXACTLY this format:
SUFFICIENT: YES or NO
NEXT_QUERY: <if NO, suggest a different, more specific search query to find missing information. If YES, write NONE>"""

    response = llm.invoke(prompt).content.strip()

    sufficient = "SUFFICIENT: YES" in response.upper()
    state["is_sufficient"] = sufficient or state["attempts"] >= 3

    if not sufficient and state["attempts"] < 3:
        # Extract the suggested next query
        for line in response.split("\n"):
            if line.upper().startswith("NEXT_QUERY:"):
                next_query = line.split(":", 1)[1].strip()
                if next_query and next_query.upper() != "NONE":
                    state["search_query"] = next_query

    print(f"[REFLECT] Sufficient: {state['is_sufficient']} | Next search query: '{state['search_query']}'")
    return state


def synthesize_node(state: AgentState) -> AgentState:
    print("[SYNTHESIZE] Generating final answer...")

    context = "\n\n".join(c["text"] for c in state["retrieved_chunks"])

    prompt = f"""Based on the following contract excerpts, answer the question clearly and cite which contract each fact comes from if relevant.

Question: {state['query']}

Contract excerpts:
{context}

Answer:"""

    response = llm.invoke(prompt)
    
    # DEBUG: inspect the full response object
    print("DEBUG - response.content:", repr(response.content))
    print("DEBUG - response.additional_kwargs:", response.additional_kwargs)
    print("DEBUG - response.response_metadata:", response.response_metadata)
    
    state["final_answer"] = response.content
    print(f"[SYNTHESIZE] Answer generated ({len(state['final_answer'])} characters)")
    return state


def should_continue(state: AgentState) -> str:
    return "synthesize" if state["is_sufficient"] else "retrieve"


def build_graph(retriever: HybridRetriever):
    graph = StateGraph(AgentState)

    graph.add_node("retrieve", lambda state: retrieve_node(state, retriever))
    graph.add_node("reflect", reflect_node)
    graph.add_node("synthesize", synthesize_node)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "reflect")
    graph.add_conditional_edges("reflect", should_continue, {
        "retrieve": "retrieve",
        "synthesize": "synthesize"
    })
    graph.add_edge("synthesize", END)

    return graph.compile()


if __name__ == "__main__":
    txt_folder = r"C:\Users\nidhi\Agentic Multi-Format Document Intelligence System\data\raw\CUAD_v1\CUAD_v1\full_contract_txt"

    contracts = load_cuad_txt_contracts(txt_folder, limit=10)
    chunks = chunk_contracts(contracts)

    retriever = HybridRetriever(chunks)
    app = build_graph(retriever)

    initial_query = "What are the termination clauses across these contracts?"
    initial_state = {
        "query": initial_query,
        "search_query": initial_query,
        "retrieved_chunks": [],
        "attempts": 0,
        "is_sufficient": False,
        "final_answer": ""
    }

    final_state = app.invoke(initial_state)

    print("\n" + "=" * 80)
    print("FINAL ANSWER:")
    print("=" * 80)
    print(final_state["final_answer"])