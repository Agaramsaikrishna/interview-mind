from src.graph import interview_graph
from src.nodes import summarize_feedback
from src.promtps import *


# #------------------------------

# # --- Main CLI ---


def main():
    print("Welcome to the AI Technical Interviewer!")

    # Multi-topic input
    raw_topics = input("Enter topics separated by commas (e.g. Python, Machine Learning, SQL): ")
    topics = [t.strip() for t in raw_topics.split(",") if t.strip()]
    if not topics:
        topics = ["General Programming"]

    rating_input = input("Rate your proficiency (1=Beginner to 10=Expert): ").strip()
    try:
        rating = int(rating_input)
        if rating < 1 or rating > 10:
            print("Invalid rating; defaulting to 5")
            rating = 5
    except ValueError:
        print("Invalid rating; defaulting to 5")
        rating = 5

    total_questions_per_topic = 3

    initial_state = {
        "topics": topics,
        "current_topic_index": 0,
        "user_proficiency_rating": rating,
        "questions_asked": [],
        "answers_given": [],
        "scores_accuracy": [],
        "scores_clarity": [],
        "scores_depth": [],
        "scores_overall": [],
        "evaluations": [],
        "follow_ups_asked": 0,
        "total_questions": total_questions_per_topic,
        "main_questions_asked": 0,
        "current_question": "",
        "current_answer": "",
        "summary" : ""
    }

    try:
        
        for state in interview_graph.stream(initial_state):
            if "ask_question" in state and "current_question" in state["ask_question"]:
                question = state["ask_question"]["current_question"]
                print("\nQuestion:", question)
            
            
            elif "summarize" in state:
                print("\n--- Final Summary ---")
                print(state["summarize"].get("summary", "No summary available."))
                
            else:
                pass
            

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
       #print("Make sure your TOGETHER_API_KEY is set.")
    finally:
        print("\n--- Interview Session Ended ---")
       
       
# to run  CLI -----------

# if __name__ == "__main__":
    # main()




#-------------------------- Streamlit UI --------------------------------------------------------------
    

import streamlit as st
import os
import re
from typing import TypedDict, List, Dict

# Assuming these are in your src folder or adjust paths accordingly
from src.config import initialize_llm
from src.state import InterviewState # Assuming InterviewState is defined in src/state.py
from src.nodes  import ask_question_streamlit ,summarize_feedback_streamlit , decide_next_step_streamlit, evaluate_answer_streamlit


# Initialize LLM (ensure initialize_llm handles API key safely)
llm = initialize_llm()




# --- Streamlit UI ---

st.set_page_config(page_title="AI Technical Interviewer", layout="centered")
st.markdown("""
<style>
    /* Import font */
    html, body, [class*="css"]  {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen,
            Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif !important;
        background-color: #f5f7fa;
    }

    /* Container styling */
    .main .block-container {
        max-width: 720px;
        margin: 2rem auto;
        padding: 2rem 2.5rem;
        background: white;
        border-radius: 12px;
        box-shadow: 0 8px 20px rgb(0 0 0 / 0.1);
        transition: box-shadow 0.3s ease;
    }
    .main .block-container:hover {
        box-shadow: 0 12px 30px rgb(0 0 0 / 0.15);
    }

    /* Headings */
    h1, h2, h3 {
        color: #1a237e;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1.5rem;
    }

    /* Buttons */
    .stButton>button {
        background-color: #2962ff; /* Bright Blue */
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.7rem 1.6rem;
        font-size: 1.1rem;
        font-weight: 700;
        cursor: pointer;
        transition: background-color 0.35s ease, transform 0.15s ease;
        box-shadow: 0 6px 15px rgb(41 98 255 / 0.3);
    }
    .stButton>button:hover {
        background-color: #0039cb;
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgb(0 57 203 / 0.5);
    }
    .stButton>button:active {
        transform: translateY(0);
        box-shadow: 0 6px 15px rgb(41 98 255 / 0.3);
    }

    /* Inputs */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea {
        border-radius: 10px;
        border: 2px solid #cfd8dc;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        font-weight: 500;
        color: #263238;
        background-color: #f9fafb;
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
        resize: vertical;
        min-height: 100px;
    }
    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus {
        outline: none;
        border-color: #2962ff;
        box-shadow: 0 0 12px rgb(41 98 255 / 0.4);
        background-color: #ffffff;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #e8eaf6;
        color: #1a237e;
        font-weight: 600;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        font-size: 0.9rem;
    }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #283593;
        margin-top: 0;
        font-weight: 700;
    }
    [data-testid="stSidebar"] .markdown-text-container p {
        font-weight: 500;
    }

    /* Chat bubbles */
    .chat-bubble {
        border-radius: 18px;
        padding: 18px 24px;
        margin-bottom: 18px;
        max-width: 80%;
        font-size: 1rem;
        line-height: 1.5;
        box-shadow: 0 3px 12px rgba(0,0,0,0.08);
        word-wrap: break-word;
        transition: background-color 0.3s ease;
    }
    .chat-bubble.user {
        background-color: #2962ff;
        color: white;
        margin-left: auto;
        box-shadow: 0 5px 18px rgba(41, 98, 255, 0.5);
    }
    .chat-bubble.ai {
        background-color: #e3eafc;
        color: #1a237e;
        margin-right: auto;
        box-shadow: 0 5px 18px rgba(41, 98, 255, 0.25);
    }

    /* Clear default margin for chat container */
    .chat-container {
        margin-bottom: 1rem;
    }

    /* Separate sections */
    .section {
        margin-bottom: 2rem;
    }

</style>
""", unsafe_allow_html=True)



st.title("👨‍💻 AI Technical Interviewer")
st.markdown("---")

# Initialize session state variables
if "interview_started" not in st.session_state:
    st.session_state.interview_started = False
if "interview_state" not in st.session_state:
    st.session_state.interview_state = {}
if "current_interview_phase" not in st.session_state:
    st.session_state.current_interview_phase = "setup" # setup, awaiting_answer, decide_next, summarize, display_summary

if not st.session_state.interview_started:
    st.subheader("Welcome! Let's get started with your interview.")

    with st.form("interview_setup"):
        raw_topics = st.text_input("Enter topics separated by commas (e.g., Python, Machine Learning, SQL)", key="topics_input")
        rating_input = st.slider("Rate your proficiency", 1, 10, 5, key="rating_input")

        submitted = st.form_submit_button("Start Interview")

        if submitted:
            topics = [t.strip() for t in raw_topics.split(",") if t.strip()]
            if not topics:
                topics = ["General Programming"]

            rating = int(rating_input) # Slider ensures valid int

            total_questions_per_topic = 3

            initial_state = {
                "topics": topics,
                "current_topic_index": 0,
                "user_proficiency_rating": rating,
                "questions_asked": [],
                "answers_given": [],
                "scores_accuracy": [],
                "scores_clarity": [],
                "scores_depth": [],
                "scores_overall": [],
                "evaluations": [],
                "follow_ups_asked": 0,
                "total_questions": total_questions_per_topic,
                "main_questions_asked": 0,
                "current_question": "",
                "current_answer": "",
                "summary": ""
            }
            st.session_state.interview_state = initial_state
            st.session_state.interview_started = True
            st.session_state.current_interview_phase = "ask_question"
            st.rerun()

elif st.session_state.interview_started:
    state = st.session_state.interview_state

    st.sidebar.header("Interview Progress")
    st.sidebar.markdown(f"**Current Topic:** {state['topics'][state['current_topic_index']]}")
  # st.sidebar.markdown(f"**Proficiency Rating:** {state['user_proficiency_rating']}/10")
  # st.sidebar.markdown(f"**Questions Asked (Current Topic):** {state['main_questions_asked']}/{state['total_questions']}")
    st.sidebar.markdown("---")
    st.sidebar.subheader("Previous Questions & Scores")
    if state["questions_asked"]:
        for i, (q, a, ovl) in enumerate(zip(state["questions_asked"], state["answers_given"], state["scores_overall"])):
            st.sidebar.markdown(f"**Q{i+1}:** {q}")
            st.sidebar.markdown(f"**A{i+1} Score:** {ovl}/10")
            st.sidebar.markdown("---")
    else:
        st.sidebar.info("No questions asked yet.")


    if st.session_state.current_interview_phase == "ask_question":
        with st.spinner("Generating question..."):
            ask_question_streamlit()
        st.rerun() # Rerun to update the display with the new question

    # if st.session_state.current_interview_phase == "awaiting_answer":
    #     st.markdown(f"<div class='chat-bubble ai'>**Question:** {state['current_question']}</div>", unsafe_allow_html=True)
    #     user_answer = st.text_area("Your Answer:", height=150, key="user_answer_input")
    #     if st.button("Submit Answer", key="submit_answer_button"):
    #         if user_answer:
    #             with st.spinner("Evaluating your answer..."):
    #                 evaluate_answer_streamlit(user_answer)
                    
    #             st.rerun()
    #         else:
    #             st.warning("Please provide an answer before submitting.")
    if st.session_state.current_interview_phase == "awaiting_answer":
        st.markdown(f"<div class='chat-bubble ai'>**Question:** {state['current_question']}</div>", unsafe_allow_html=True)

        with st.form("answer_form", clear_on_submit=True):
            user_answer = st.text_area("Your Answer:", height=150, key="user_answer_input")
            submitted = st.form_submit_button("Submit Answer")

        if submitted:
            if user_answer and user_answer.strip():
                with st.spinner("Evaluating your answer..."):
                    evaluate_answer_streamlit(user_answer.strip())
                st.rerun()
            else:
                st.warning("Please provide an answer before submitting.")

    if st.session_state.current_interview_phase == "decide_next":
        # Display the last evaluation
        st.markdown(f"<div class='chat-bubble user'>**Your Answer:** {state['answers_given'][-1]}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='chat-bubble ai'>**Evaluation:** {state['evaluations'][-1]}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='chat-bubble ai'>**Overall Score:** {state['scores_overall'][-1]}/10</div>", unsafe_allow_html=True)

        decide_next_step_streamlit()
        st.rerun() # Rerun to move to the next phase (ask_question, summarize, or next topic message)

    if st.session_state.current_interview_phase == "summarize":
        with st.spinner("Generating final summary..."):
            summarize_feedback_streamlit()
        st.rerun()

    if st.session_state.current_interview_phase == "display_summary":
        st.markdown("---")
        st.header("✨ Interview Summary")
        st.write(st.session_state.interview_state["summary"])

        # Display average scores
        def avg(lst): return sum(lst) / len(lst) if lst else 0
        avg_acc = avg(st.session_state.interview_state["scores_accuracy"])
        avg_clr = avg(st.session_state.interview_state["scores_clarity"])
        avg_dep = avg(st.session_state.interview_state["scores_depth"])
        avg_ovl = avg(st.session_state.interview_state["scores_overall"])

        st.subheader("Average Scores Across Interview")
        st.markdown(f"- **Accuracy:** {avg_acc:.1f}/10")
        st.markdown(f"- **Clarity:** {avg_clr:.1f}/10")
        st.markdown(f"- **Depth:** {avg_dep:.1f}/10")
        st.markdown(f"- **Overall:** {avg_ovl:.1f}/10")

        if st.button("Start New Interview"):
            st.session_state.clear()
            st.rerun()

st.markdown("---")
st.info("💡 Tip: Refresh the page to start a new interview at any time.")