import os
import re
from typing import TypedDict, List, Dict
from src.config import initialize_llm
from src.promtps import *
from src.state import InterviewState

llm = initialize_llm()


# --- Functions ---

def ask_question(state: InterviewState) -> InterviewState:
    topic = state["topics"][state["current_topic_index"]]
    rating = state["user_proficiency_rating"]

    # If follow-up needed and none asked
    if (state["scores_overall"] and state["scores_overall"][-1] < 6 and state["follow_ups_asked"] == 0 and
        state["main_questions_asked"] > 0):
        prompt_messages = follow_up_prompt.format_messages(
            previous_question=state["current_question"],
            previous_answer=state["current_answer"], 
            topic=topic,
            rating=rating
        )
        question = llm.invoke(prompt_messages).content.strip()
        state["follow_ups_asked"] = 1
    else:
        # New main question
        state["follow_ups_asked"] = 0
        state["main_questions_asked"] += 1

        prev_qs = "\n".join(state["questions_asked"])
        prompt_messages = interviewer_prompt.format_messages(
            topic=topic,
            rating=rating,
            previous_questions=prev_qs if prev_qs else "None"
        )
        question = llm.invoke(prompt_messages).content.strip()

    # print(f"\n[{topic}] Question: {question}")
    state["current_question"] = question
    state["questions_asked"].append(question)
    #print(state)
    return state

def receive_answer(state: InterviewState) -> InterviewState:
    #print("\n--- Candidate ---")
    # answer = input(" Your Answer: ")
    # state["current_answer"] = answer
    # state["answers_given"].append(answer)
    return state

def evaluate_answer(state: InterviewState) -> InterviewState:
    prompt_messages = detailed_evaluation_prompt.format_messages(
        question=state["current_question"],
        answer=state["current_answer"]
    )
    eval_resp = llm.invoke(prompt_messages).content.strip()
    #  print(f"\n📊 Evaluation:\n{eval_resp}")
    state["evaluations"].append(eval_resp)

    # Parse scores from response
    scores = {"Accuracy": 0, "Clarity": 0, "Depth": 0, "Overall": 0}
    for key in scores.keys():
        pattern = rf"{key}:\s*(\d+)"
        match = re.search(pattern, eval_resp, re.IGNORECASE)
        if match:
            scores[key] = int(match.group(1))
    state["scores_accuracy"].append(scores["Accuracy"])
    state["scores_clarity"].append(scores["Clarity"])
    state["scores_depth"].append(scores["Depth"])
    state["scores_overall"].append(scores["Overall"])

    return state

def decide_next_step(state: InterviewState) -> str:
    # If last overall score < 6 and follow-up not asked => ask follow-up
    if state["scores_overall"] and state["scores_overall"][-1] < 6 and state["follow_ups_asked"] == 0:
        return "ask_question"
    # If less than total questions for this topic, ask next main question
    if state["main_questions_asked"] < state["total_questions"]:
        return "ask_question"
    # Else move to next topic or summarize
    if state["current_topic_index"] + 1 < len(state["topics"]):
        state["current_topic_index"] += 1
        # Reset counters for new topic
        state["questions_asked"].clear()
        state["answers_given"].clear()
        state["scores_accuracy"].clear()
        state["scores_clarity"].clear()
        state["scores_depth"].clear()
        state["scores_overall"].clear()
        state["evaluations"].clear()
        state["follow_ups_asked"] = 0
        state["main_questions_asked"] = 0
        print(f"\n\n Moving to next topic: {state['topics'][state['current_topic_index']]}")
        return "ask_question"
    else:
        return "summarize"

def summarize_feedback(state: InterviewState) -> Dict:
    # Compile full transcript including topics
    transcript_lines = []
    for i, (q, a, acc, clr, dep, ovl, ev) in enumerate(zip(
            state["questions_asked"], state["answers_given"],
            state["scores_accuracy"], state["scores_clarity"],
            state["scores_depth"], state["scores_overall"],
            state["evaluations"])):
        transcript_lines.append(f"Q{i+1}: {q}")
        transcript_lines.append(f"A{i+1}: {a}")
        transcript_lines.append(f"Accuracy: {acc}/10, Clarity: {clr}/10, Depth: {dep}/10, Overall: {ovl}/10")
        transcript_lines.append(f"Evaluation: {ev}\n")
    transcript = "\n".join(transcript_lines)

    # Calculate averages per score category
    def avg(lst): return sum(lst) / len(lst) if lst else 0
    avg_acc = avg(state["scores_accuracy"])
    avg_clr = avg(state["scores_clarity"])
    avg_dep = avg(state["scores_depth"])
    avg_ovl = avg(state["scores_overall"])

    summary_messages = summary_prompt.format_messages(transcript=transcript)
    summary_text = llm.invoke(summary_messages).content.strip()

    # print("\n--- Final Interview Summary ---")
    # print(f"Average Accuracy: {avg_acc:.1f}/10")
    # print(f"Average Clarity: {avg_clr:.1f}/10")
    # print(f"Average Depth: {avg_dep:.1f}/10")
    # print(f"Average Overall: {avg_ovl:.1f}/10\n")
    # print(summary_text)

    state['summary']=summary_text
    return state
    #return {"summary": summary_text, "averages": (avg_acc, avg_clr, avg_dep, avg_ovl)}
    

import streamlit as st
import os
import re
from typing import TypedDict, List, Dict

# Assuming these are in your src folder or adjust paths accordingly
from src.config import initialize_llm
from src.state import InterviewState # Assuming InterviewState is defined in src/state.py

# Initialize LLM (ensure initialize_llm handles API key safely)
llm = initialize_llm()

# --- Functions (adapted for Streamlit session state) ---

def ask_question_streamlit():
    """Asks a new question or a follow-up question."""
    if "interview_state" not in st.session_state:
        return

    state = st.session_state.interview_state
    topic = state["topics"][state["current_topic_index"]]
    rating = state["user_proficiency_rating"]

    # If follow-up needed and none asked
    if (state["scores_overall"] and state["scores_overall"][-1] < 6 and state["follow_ups_asked"] == 0 and
            state["main_questions_asked"] > 0):
        prompt_messages = follow_up_prompt.format_messages(
            previous_question=state["current_question"],
            previous_answer=state["current_answer"],
            topic=topic,
            rating=rating
        )
        question = llm.invoke(prompt_messages).content.strip()
        state["follow_ups_asked"] = 1
    else:
        # New main question
        state["follow_ups_asked"] = 0
        state["main_questions_asked"] += 1

        prev_qs = "\n".join(state["questions_asked"])
        prompt_messages = interviewer_prompt.format_messages(
            topic=topic,
            rating=rating,
            previous_questions=prev_qs if prev_qs else "None"
        )
        question = llm.invoke(prompt_messages).content.strip()

    state["current_question"] = question
    state["questions_asked"].append(question)
    st.session_state.interview_state = state
    st.session_state.current_interview_phase = "awaiting_answer"

def evaluate_answer_streamlit(answer: str):
    """Evaluates the given answer."""
    if "interview_state" not in st.session_state:
        return

    state = st.session_state.interview_state
    state["current_answer"] = answer
    state["answers_given"].append(answer)

    prompt_messages = detailed_evaluation_prompt.format_messages(
        question=state["current_question"],
        answer=state["current_answer"]
    )
    eval_resp = llm.invoke(prompt_messages).content.strip()
    state["evaluations"].append(eval_resp)

    # Parse scores from response
    scores = {"Accuracy": 0, "Clarity": 0, "Depth": 0, "Overall": 0}
    for key in scores.keys():
        pattern = rf"{key}:\s*(\d+)"
        match = re.search(pattern, eval_resp, re.IGNORECASE)
        if match:
            scores[key] = int(match.group(1))
    state["scores_accuracy"].append(scores["Accuracy"])
    state["scores_clarity"].append(scores["Clarity"])
    state["scores_depth"].append(scores["Depth"])
    state["scores_overall"].append(scores["Overall"])

    st.session_state.interview_state = state
    st.session_state.current_interview_phase = "decide_next"


def decide_next_step_streamlit():
    """Decides whether to ask next question, move to next topic, or summarize."""
    if "interview_state" not in st.session_state:
        return

    state = st.session_state.interview_state

    # If last overall score < 6 and follow-up not asked => ask follow-up
    if state["scores_overall"] and state["scores_overall"][-1] < 6 and state["follow_ups_asked"] == 0:
        st.session_state.current_interview_phase = "ask_question"
        return

    # If less than total questions for this topic, ask next main question
    if state["main_questions_asked"] < state["total_questions"]:
        st.session_state.current_interview_phase = "ask_question"
        return

    # Else move to next topic or summarize
    if state["current_topic_index"] + 1 < len(state["topics"]):
        state["current_topic_index"] += 1
        # Reset counters for new topic
        state["questions_asked"].clear()
        state["answers_given"].clear()
        state["scores_accuracy"].clear()
        state["scores_clarity"].clear()
        state["scores_depth"].clear()
        state["scores_overall"].clear()
        state["evaluations"].clear()
        state["follow_ups_asked"] = 0
        state["main_questions_asked"] = 0
        st.session_state.interview_state = state
        st.session_state.current_interview_phase = "ask_question"
        st.info(f"Moving to next topic: **{state['topics'][state['current_topic_index']]}**")
    else:
        st.session_state.current_interview_phase = "summarize"


def summarize_feedback_streamlit():
    """Generates a summary of the interview."""
    if "interview_state" not in st.session_state:
        return

    state = st.session_state.interview_state

    # Compile full transcript
    transcript_lines = []
    for i, (q, a, acc, clr, dep, ovl, ev) in enumerate(zip(
            state["questions_asked"], state["answers_given"],
            state["scores_accuracy"], state["scores_clarity"],
            state["scores_depth"], state["scores_overall"],
            state["evaluations"])):
        transcript_lines.append(f"Q{i+1}: {q}")
        transcript_lines.append(f"A{i+1}: {a}")
        transcript_lines.append(f"Accuracy: {acc}/10, Clarity: {clr}/10, Depth: {dep}/10, Overall: {ovl}/10")
        transcript_lines.append(f"Evaluation: {ev}\n")
    transcript = "\n".join(transcript_lines)

    summary_messages = summary_prompt.format_messages(transcript=transcript)
    summary_text = llm.invoke(summary_messages).content.strip()

    state['summary'] = summary_text
    st.session_state.interview_state = state
    st.session_state.current_interview_phase = "display_summary"