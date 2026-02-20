"""LangGraph interview orchestration service."""

import logging
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.models.schemas import InterviewQuestion
from app.prompts.interview import CORE_QUESTIONS

logger = logging.getLogger(__name__)

# ---------- Pre-fill mapping: question_id -> (enrichment_field, context_hint_template) ----------

ENRICHMENT_PREFILL_MAP: dict[str, tuple[str, str]] = {
    "core_1": ("products_description", "Baseado no seu site: {value}"),
    "core_2": ("payment_methods_mentioned", "Encontrado no site: {value}"),
    "core_5": ("communication_tone", "Tom detectado no site: {value}"),
}


# ---------- State ----------


class InterviewState(TypedDict):
    enrichment_data: dict
    core_questions_remaining: list[dict]
    current_question: dict | None
    answers: list[dict]
    dynamic_questions_asked: int
    max_dynamic_questions: int
    phase: str  # "core" | "dynamic" | "defaults" | "complete"
    needs_follow_up: bool
    follow_up_question: dict | None


# ---------- Pre-fill helper ----------


def _apply_enrichment_prefill(question: dict, enrichment_data: dict) -> dict:
    """Apply enrichment-based pre-fill to a question dict if applicable."""
    qid = question.get("question_id", "")
    mapping = ENRICHMENT_PREFILL_MAP.get(qid)
    if not mapping:
        return question

    field, hint_template = mapping
    value = enrichment_data.get(field, "")
    if value and isinstance(value, str) and value.strip():
        question = {**question}  # shallow copy to avoid mutating original
        question["pre_filled_value"] = value.strip()
        question["context_hint"] = hint_template.format(value=value.strip())

    return question


# ---------- Graph node functions ----------


def initialize(state: InterviewState) -> dict:
    """Load core questions into state and set initial values."""
    return {
        "core_questions_remaining": [q.model_dump() for q in CORE_QUESTIONS],
        "current_question": None,
        "answers": [],
        "dynamic_questions_asked": 0,
        "max_dynamic_questions": 8,
        "phase": "core",
        "needs_follow_up": False,
        "follow_up_question": None,
    }


def select_next_core_question(state: InterviewState) -> dict:
    """Pop the next core question from remaining and apply enrichment pre-fill."""
    remaining = list(state["core_questions_remaining"])

    if not remaining:
        logger.info("All core questions answered, transitioning to dynamic phase")
        return {
            "core_questions_remaining": [],
            "current_question": None,
            "phase": "dynamic",
        }

    next_q = remaining.pop(0)
    next_q = _apply_enrichment_prefill(next_q, state.get("enrichment_data", {}))

    return {
        "core_questions_remaining": remaining,
        "current_question": next_q,
    }


def present_question(state: InterviewState) -> dict:
    """No-op passthrough — extension point for future tasks."""
    return {}


def route_after_select(state: InterviewState) -> str:
    """Route to present_question if a question was selected, otherwise END."""
    if state.get("current_question") is not None:
        return "present_question"
    return END


# ---------- Graph builders ----------


def _build_full_graph() -> StateGraph:
    """Build the complete interview graph (initialize + select + present)."""
    graph = StateGraph(InterviewState)
    graph.add_node("initialize", initialize)
    graph.add_node("select_next_core_question", select_next_core_question)
    graph.add_node("present_question", present_question)

    graph.add_edge(START, "initialize")
    graph.add_edge("initialize", "select_next_core_question")
    graph.add_conditional_edges(
        "select_next_core_question",
        route_after_select,
        {"present_question": "present_question", END: END},
    )
    graph.add_edge("present_question", END)

    return graph


def _build_next_question_graph() -> StateGraph:
    """Build the graph that only selects and presents the next question."""
    graph = StateGraph(InterviewState)
    graph.add_node("select_next_core_question", select_next_core_question)
    graph.add_node("present_question", present_question)

    graph.add_edge(START, "select_next_core_question")
    graph.add_conditional_edges(
        "select_next_core_question",
        route_after_select,
        {"present_question": "present_question", END: END},
    )
    graph.add_edge("present_question", END)

    return graph


# ---------- Serialization ----------


def serialize_state(state: InterviewState) -> dict:
    """Convert InterviewState to a JSON-serializable dict for DB storage."""
    return dict(state)


def deserialize_state(data: dict) -> InterviewState:
    """Restore InterviewState from a JSON dict loaded from DB."""
    return InterviewState(
        enrichment_data=data.get("enrichment_data", {}),
        core_questions_remaining=data.get("core_questions_remaining", []),
        current_question=data.get("current_question"),
        answers=data.get("answers", []),
        dynamic_questions_asked=data.get("dynamic_questions_asked", 0),
        max_dynamic_questions=data.get("max_dynamic_questions", 8),
        phase=data.get("phase", "core"),
        needs_follow_up=data.get("needs_follow_up", False),
        follow_up_question=data.get("follow_up_question"),
    )


# ---------- Public API ----------


async def create_interview(enrichment_data: dict | None = None) -> InterviewState:
    """Create a fresh interview state and advance to the first question.

    Args:
        enrichment_data: CompanyProfile dict from enrichment, or None.

    Returns:
        InterviewState with phase="core", current_question set to core_1,
        and 11 remaining core questions.
    """
    initial_state: InterviewState = {
        "enrichment_data": enrichment_data or {},
        "core_questions_remaining": [],
        "current_question": None,
        "answers": [],
        "dynamic_questions_asked": 0,
        "max_dynamic_questions": 8,
        "phase": "core",
        "needs_follow_up": False,
        "follow_up_question": None,
    }

    graph = _build_full_graph().compile()
    result = graph.invoke(initial_state)
    return InterviewState(**result)


async def submit_answer(
    state: InterviewState,
    question_id: str,
    answer: str,
    source: str = "text",
) -> tuple[InterviewQuestion | None, InterviewState]:
    """Store an answer and advance to the next question.

    Args:
        state: Current InterviewState (loaded from DB).
        question_id: ID of the question being answered (must match current_question).
        answer: The user's answer text.
        source: "text" or "audio".

    Returns:
        Tuple of (next InterviewQuestion or None, updated InterviewState).

    Raises:
        ValueError: If question_id doesn't match the current question.
    """
    current = state.get("current_question")
    if current is None or current.get("question_id") != question_id:
        expected = current.get("question_id") if current else "none"
        raise ValueError(
            f"Question ID mismatch: expected '{expected}', got '{question_id}'"
        )

    # Store the answer
    answers = list(state["answers"])
    answers.append({
        "question_id": question_id,
        "answer": answer,
        "source": source,
        "question_text": current.get("question_text", ""),
    })

    # Update state with the answer before advancing
    updated_state = InterviewState(
        enrichment_data=state["enrichment_data"],
        core_questions_remaining=state["core_questions_remaining"],
        current_question=state["current_question"],
        answers=answers,
        dynamic_questions_asked=state["dynamic_questions_asked"],
        max_dynamic_questions=state["max_dynamic_questions"],
        phase=state["phase"],
        needs_follow_up=state["needs_follow_up"],
        follow_up_question=state["follow_up_question"],
    )

    # Advance to next question
    return await get_next_question(updated_state)


async def get_next_question(
    state: InterviewState,
) -> tuple[InterviewQuestion | None, InterviewState]:
    """Advance the interview to the next core question.

    Args:
        state: Current InterviewState (loaded from DB).

    Returns:
        Tuple of (next InterviewQuestion or None if no more core questions,
        updated InterviewState).
    """
    graph = _build_next_question_graph().compile()
    result = graph.invoke(dict(state))
    new_state = InterviewState(**result)

    current = new_state.get("current_question")
    if current is not None:
        question = InterviewQuestion.model_validate(current)
        return question, new_state

    return None, new_state
