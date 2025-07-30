from typing import TypedDict, List, Dict



# --- Interview State ---

class InterviewState(TypedDict):
    topics: List[str]                      # List of topics, multi-topic support
    current_topic_index: int               # Which topic are we on now
    user_proficiency_rating: int
    questions_asked: List[str]
    answers_given: List[str]
    scores_accuracy: List[int]
    scores_clarity: List[int]
    scores_depth: List[int]
    scores_overall: List[int]
    evaluations: List[str]
    follow_ups_asked: int                  # for current question slot, 0 or 1
    total_questions: int                   # questions per topic
    main_questions_asked: int              # number of main questions asked in current topic
    current_question: str
    current_answer: str
    summary : str