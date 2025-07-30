
from langgraph.graph import StateGraph, END
from src.promtps import *
from src.state import InterviewState
from src.nodes import ask_question, receive_answer, evaluate_answer , decide_next_step , summarize_feedback

# --- LangGraph setup ---

workflow = StateGraph(InterviewState)

workflow.add_node("ask_question", ask_question)
workflow.add_node("receive_answer", receive_answer)
workflow.add_node("evaluate", evaluate_answer)
workflow.add_node("decide_next_step", decide_next_step)
workflow.add_node("summarize", summarize_feedback)

workflow.set_entry_point("ask_question")

workflow.add_edge("ask_question", "receive_answer")
workflow.add_edge("receive_answer", "evaluate")
workflow.add_conditional_edges(
    "evaluate",
    decide_next_step,
    {
        "ask_question": "ask_question",
        "summarize": "summarize"
    }
)
workflow.add_edge("summarize", END)

interview_graph = workflow.compile()