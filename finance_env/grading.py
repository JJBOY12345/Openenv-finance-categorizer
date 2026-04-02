"""Deterministic graders for the finance categorization environment."""

from __future__ import annotations

from typing import Mapping

from .models import CategoryName, FinanceGraderResult, FinanceState


def grade_categorization_task(
    state: FinanceState,
    answer_key: Mapping[str, CategoryName],
) -> FinanceGraderResult:
    """Grade a categorization task deterministically from public state plus hidden labels."""

    total_transactions = len(state.transaction_queue)
    categorized_count = len(state.processed_entries)
    correct_count = sum(
        1
        for transaction_id, entry in state.processed_entries.items()
        if answer_key.get(transaction_id) == entry.assigned_category
    )
    categorized_accuracy = correct_count / categorized_count if categorized_count else 0.0
    completion_ratio = categorized_count / total_transactions if total_transactions else 0.0
    invalid_action_rate = state.invalid_action_count / max(state.step_count, 1)
    premature_finalize = state.finalized and categorized_count < total_transactions

    raw_score = (
        0.7 * categorized_accuracy
        + 0.2 * completion_ratio
        + (0.1 if state.finalized and not premature_finalize else 0.0)
        - (0.1 if premature_finalize else 0.0)
        - 0.05 * invalid_action_rate
    )
    score = max(0.0, min(1.0, round(raw_score, 4)))

    notes: list[str] = []
    if categorized_count == 0:
        notes.append("No transactions were categorized.")
    if premature_finalize:
        notes.append("Episode was finalized before all transactions were processed.")
    if state.invalid_action_count:
        notes.append(f"Episode included {state.invalid_action_count} invalid action(s).")

    return FinanceGraderResult(
        score=score,
        categorized_accuracy=round(categorized_accuracy, 4),
        completion_ratio=round(completion_ratio, 4),
        finalized=state.finalized,
        premature_finalize=premature_finalize,
        invalid_action_rate=round(min(invalid_action_rate, 1.0), 4),
        notes=notes,
    )


def grade_easy_task(
    state: FinanceState,
    answer_key: Mapping[str, CategoryName],
) -> FinanceGraderResult:
    """Grade the easy task using the shared categorization rubric."""

    return grade_categorization_task(state=state, answer_key=answer_key)


def grade_medium_task(
    state: FinanceState,
    answer_key: Mapping[str, CategoryName],
) -> FinanceGraderResult:
    """Grade the medium task using the shared categorization rubric."""

    return grade_categorization_task(state=state, answer_key=answer_key)


def grade_hard_task(
    state: FinanceState,
    answer_key: Mapping[str, CategoryName],
) -> FinanceGraderResult:
    """Grade the hard task using the shared categorization rubric."""

    return grade_categorization_task(state=state, answer_key=answer_key)
