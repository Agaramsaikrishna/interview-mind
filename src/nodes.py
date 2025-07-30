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

# def ask_question_streamlit():
#     """Asks a new question or a follow-up question."""
#     if "interview_state" not in st.session_state:
#         return

#     state = st.session_state.interview_state
#     topic = state["topics"][state["current_topic_index"]]
#     rating = state["user_proficiency_rating"]

#     # If follow-up needed and none asked
#     if (state["scores_overall"] and state["scores_overall"][-1] < 6 and state["follow_ups_asked"] == 0 and
#             state["main_questions_asked"] > 0):
#         prompt_messages = follow_up_prompt.format_messages(
#             previous_question=state["current_question"],
#             previous_answer=state["current_answer"],
#             topic=topic,
#             rating=rating
#         )
#         question = llm.invoke(prompt_messages).content.strip()
#         state["follow_ups_asked"] = 1
#     else:
#         # New main question
#         state["follow_ups_asked"] = 0
#         state["main_questions_asked"] += 1

#         prev_qs = "\n".join(state["questions_asked"])
#         prompt_messages = interviewer_prompt.format_messages(
#             topic=topic,
#             rating=rating,
#             previous_questions=prev_qs if prev_qs else "None"
#         )
#         question = llm.invoke(prompt_messages).content.strip()

#     state["current_question"] = question
#     state["questions_asked"].append(question)
#     st.session_state.interview_state = state
#     st.session_state.current_interview_phase = "awaiting_answer"
# In src/nodes.py or where your streamlit functions are

def ask_question_streamlit():
    """Asks a new question or a follow-up question."""
    if "interview_state" not in st.session_state:
        return

    state = st.session_state.interview_state
    topic = state["topics"][state["current_topic_index"]]
    rating = state["user_proficiency_rating"]

    # Decide if it's a follow-up or a new main question
    is_follow_up = (
        state["scores_overall"] and
        state["scores_overall"][-1] < 6 and # Candidate struggled (score < 6)
        state["follow_ups_asked"] == 0 and  # Haven't asked a follow-up yet for this question
        state["main_questions_asked"] > 0   # Not the very first question
    )

    if is_follow_up:
        prompt_messages = follow_up_prompt.format_messages(
            previous_question=state["current_question"], # These are now correctly provided for follow-ups
            previous_answer=state["current_answer"],
            topic=topic,
            rating=rating
        )
        question = llm.invoke(prompt_messages).content.strip()
        state["follow_ups_asked"] = 1 # Mark that a follow-up has been asked
    else:
        # This branch is for new main questions (either initial or subsequent ones after a good answer)
        state["follow_ups_asked"] = 0 # Reset for new main question
        state["main_questions_asked"] += 1

        prompt_messages = interviewer_prompt.format_messages(
            topic=topic,
            rating=rating,
            # No previous_question/previous_answer needed here anymore!
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


# def decide_next_step_streamlit():
#     """Decides whether to ask next question, move to next topic, or summarize."""
#     if "interview_state" not in st.session_state:
#         return

#     state = st.session_state.interview_state

#     # If last overall score < 6 and follow-up not asked => ask follow-up
#     if state["scores_overall"] and state["scores_overall"][-1] < 6 and state["follow_ups_asked"] == 0:
#         st.session_state.current_interview_phase = "ask_question"
#         return

#     # If less than total questions for this topic, ask next main question
#     if state["main_questions_asked"] < state["total_questions"]:
#         st.session_state.current_interview_phase = "ask_question"
#         return

#     # Else move to next topic or summarize
#     if state["current_topic_index"] + 1 < len(state["topics"]):
#         state["current_topic_index"] += 1
#         # Reset counters for new topic
#         state["questions_asked"].clear()
#         state["answers_given"].clear()
#         state["scores_accuracy"].clear()
#         state["scores_clarity"].clear()
#         state["scores_depth"].clear()
#         state["scores_overall"].clear()
#         state["evaluations"].clear()
#         state["follow_ups_asked"] = 0
#         state["main_questions_asked"] = 0
#         st.session_state.interview_state = state
#         st.session_state.current_interview_phase = "ask_question"
#         st.info(f"Moving to next topic: **{state['topics'][state['current_topic_index']]}**")
#     else:
#         st.session_state.current_interview_phase = "summarize"

# In src/nodes.py or where your streamlit functions are

def decide_next_step_streamlit():
    """Decides whether to ask next question, move to next topic, or summarize."""
    if "interview_state" not in st.session_state:
        return

    state = st.session_state.interview_state

    # Check if candidate struggled and a follow-up hasn't been asked yet for this question
    if state["scores_overall"] and state["scores_overall"][-1] < 6 and state["follow_ups_asked"] == 0:
        st.session_state.current_interview_phase = "ask_question" # Go back to ask_question, which will now trigger a follow-up
        return

    # If we've asked enough main questions for the current topic
    if state["main_questions_asked"] < state["total_questions"]:
        st.session_state.current_interview_phase = "ask_question" # Ask another main question
        return

    # Otherwise, move to the next topic or summarize
    if state["current_topic_index"] + 1 < len(state["topics"]):
        state["current_topic_index"] += 1
        # Reset counters for the new topic
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
        
        
        
# def summarize_feedback_streamlit():
#     """Generates a summary of the interview."""
#     if "interview_state" not in st.session_state:
#         return

#     state = st.session_state.interview_state

#     # Compile full transcript
#     transcript_lines = []
#     for i, (q, a, acc, clr, dep, ovl, ev) in enumerate(zip(
#             state["questions_asked"], state["answers_given"],
#             state["scores_accuracy"], state["scores_clarity"],
#             state["scores_depth"], state["scores_overall"],
#             state["evaluations"])):
#         transcript_lines.append(f"Q{i+1}: {q}")
#         transcript_lines.append(f"A{i+1}: {a}")
#         transcript_lines.append(f"Accuracy: {acc}/10, Clarity: {clr}/10, Depth: {dep}/10, Overall: {ovl}/10")
#         transcript_lines.append(f"Evaluation: {ev}\n")
#     transcript = "\n".join(transcript_lines)

#     summary_messages = summary_prompt.format_messages(transcript=transcript)
#     summary_text = llm.invoke(summary_messages).content.strip()

#     state['summary'] = summary_text
#     st.session_state.interview_state = state
#     st.session_state.current_interview_phase = "display_summary"



import numpy as np
import re # Import regex module

def summarize_feedback_streamlit():
    """Generates a summary of the interview and displays it."""
    if "interview_state" not in st.session_state:
        return

    state = st.session_state.interview_state

    # Compile full transcript - Ensure individual scores are NOT in this transcript
    transcript_lines = []
    for i, (q, a, ev) in enumerate(zip(
            state["questions_asked"], state["answers_given"],
            state["evaluations"])):
        transcript_lines.append(f"Q{i+1}: {q}")
        transcript_lines.append(f"A{i+1}: {a}")
        # Make sure individual scores like "Accuracy: X/10" are NOT appended here
        transcript_lines.append(f"Evaluation: {ev}\n")
    transcript = "\n".join(transcript_lines)

    # Calculate averages in Python
    avg_accuracy = np.mean(state["scores_accuracy"]) if state["scores_accuracy"] else 0
    avg_clarity = np.mean(state["scores_clarity"]) if state["scores_clarity"] else 0
    avg_depth = np.mean(state["scores_depth"]) if state["scores_depth"] else 0
    avg_overall = np.mean(state["scores_overall"]) if state["scores_overall"] else 0

    summary_messages = summary_prompt.format_messages(
        transcript=transcript,
        avg_accuracy=avg_accuracy,
        avg_clarity=avg_clarity,
        avg_depth=avg_depth,
        avg_overall=avg_overall
    )
    raw_summary_text = llm.invoke(summary_messages).content.strip()

    # --- New: Parse the structured output ---
    parsed_summary = {}
    current_section = None
    # Use re.split to split the raw_summary_text by headings
    # This pattern captures the heading itself and the content following it
    sections = re.split(r'^(##\s+.*)$', raw_summary_text, flags=re.MULTILINE)

    # The first element might be empty if the text starts with a heading
    # or it might be content before the first heading.
    # We are only interested in content under explicit headings.
    for i in range(len(sections)):
        if sections[i].strip().startswith("##"):
            # This is a heading line
            current_section = sections[i].strip().replace("## ", "").strip()
            parsed_summary[current_section] = ""
        elif current_section:
            # This is content for the current section
            parsed_summary[current_section] += sections[i].strip() + "\n"

    # Display the parsed sections in Streamlit
    st.markdown("## Interview Summary") # Overall title
    if "Average Scores" in parsed_summary:
        st.markdown("### Average Scores") # Use a sub-heading for display
        st.text(parsed_summary["Average Scores"].strip()) # Use st.text to preserve formatting

    if "Strengths" in parsed_summary:
        st.markdown("### Strengths")
        st.markdown(parsed_summary["Strengths"].strip())

    if "Areas for Improvement" in parsed_summary:
        st.markdown("### Areas for Improvement")
        st.markdown(parsed_summary["Areas for Improvement"].strip())

    if "Actionable Learning Advice" in parsed_summary:
        st.markdown("### Actionable Learning Advice")
        st.markdown(parsed_summary["Actionable Learning Advice"].strip())

    state['summary'] = raw_summary_text # Store the raw summary, or parsed if you prefer
    st.session_state.interview_state = state
    st.session_state.current_interview_phase = "display_summary"