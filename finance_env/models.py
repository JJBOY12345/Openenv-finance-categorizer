# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the finance categorization environment.

The first implementation supports a deterministic easy task where an agent
categorizes straightforward personal finance transactions and then finalizes
the ledger.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from openenv.core.env_server.types import Action, Observation, State
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

EPS = 0.01


def safe_open_interval(x: float) -> float:
    """Clamp validator-visible score and reward values into a printable-safe open interval."""

    return max(EPS, min(1.0 - EPS, x))


class FinanceBaseModel(BaseModel):
    """Common config for typed finance support models."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class CategoryName(str, Enum):
    """Allowed transaction categories for v1 of the environment."""

    GROCERIES = "groceries"
    DINING = "dining"
    TRANSPORT = "transport"
    UTILITIES = "utilities"
    RENT = "rent"
    SUBSCRIPTIONS = "subscriptions"
    HEALTHCARE = "healthcare"
    SHOPPING = "shopping"
    TRAVEL = "travel"
    ENTERTAINMENT = "entertainment"
    TRANSFER = "transfer"
    INCOME = "income"
    FEES = "fees"
    UNCATEGORIZED = "uncategorized"


class DifficultyLevel(str, Enum):
    """Difficulty levels reserved for the task ladder."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ActionType(str, Enum):
    """Supported action types for the first environment pass."""

    CATEGORIZE_TRANSACTION = "categorize_transaction"
    FINALIZE = "finalize"


class TransactionRecord(FinanceBaseModel):
    """Visible transaction data provided to the agent."""

    transaction_id: str = Field(..., description="Stable identifier for the transaction")
    merchant: str = Field(..., description="Normalized merchant or counterparty name")
    amount: float = Field(..., description="Signed transaction amount")
    currency: str = Field(default="USD", description="Transaction currency")
    posted_date: str = Field(..., description="Posting date in YYYY-MM-DD format")
    memo: str = Field(default="", description="Additional transaction description")
    channel: str = Field(default="card", description="Payment channel")


class LedgerEntry(FinanceBaseModel):
    """Processed transaction entry stored in the ledger."""

    transaction_id: str = Field(..., description="Stable identifier for the transaction")
    assigned_category: CategoryName = Field(..., description="Assigned category")
    amount: float = Field(..., description="Processed transaction amount")
    merchant: str = Field(..., description="Merchant name copied for auditability")
    note: Optional[str] = Field(default=None, description="Optional operator note")


class RewardBreakdown(FinanceBaseModel):
    """Typed reward components kept for auditability and grading work later."""

    correctness_reward: float = Field(default=0.0)
    invalid_action_penalty: float = Field(default=0.0)
    finalize_bonus: float = Field(default=0.0)
    premature_finalize_penalty: float = Field(default=0.0)
    step_penalty: float = Field(default=0.0)


class FinanceReward(FinanceBaseModel):
    """Typed reward record aligned with the scalar reward returned by OpenEnv."""

    value: float = Field(
        ...,
        gt=0.0,
        lt=1.0,
        description="Net reward for the last environment step, strictly bounded within (0, 1)",
    )
    breakdown: RewardBreakdown = Field(
        default_factory=RewardBreakdown,
        description="Decomposed reward components for debugging",
    )
    reason: str = Field(default="", description="Short explanation of the reward")

    @field_validator("value")
    @classmethod
    def validate_open_interval_value(cls, value: float) -> float:
        """Reject exact boundary rewards at the model boundary."""

        return safe_open_interval(value)


class ActionHistoryEntry(FinanceBaseModel):
    """Compact action log entry for observation and debugging."""

    step_index: int = Field(..., ge=1)
    action_type: ActionType = Field(...)
    transaction_id: Optional[str] = Field(default=None)
    category: Optional[CategoryName] = Field(default=None)
    outcome: str = Field(..., description="Human-readable result summary")


class LedgerSummary(FinanceBaseModel):
    """Aggregated ledger progress exposed to the agent."""

    processed_count: int = Field(default=0, ge=0)
    unresolved_count: int = Field(default=0, ge=0)
    category_counts: Dict[CategoryName, int] = Field(default_factory=dict)


class FinanceGraderResult(FinanceBaseModel):
    """Deterministic grading output for a completed or partial episode."""

    score: float = Field(..., gt=0.0, lt=1.0)
    categorized_accuracy: float = Field(..., gt=0.0, lt=1.0)
    completion_ratio: float = Field(..., gt=0.0, lt=1.0)
    finalized: bool = Field(..., description="Whether the episode was finalized")
    premature_finalize: bool = Field(
        ..., description="Whether finalize occurred before all transactions were processed"
    )
    invalid_action_rate: float = Field(..., gt=0.0, lt=1.0)
    notes: List[str] = Field(default_factory=list)

    @field_validator(
        "score",
        "categorized_accuracy",
        "completion_ratio",
        "invalid_action_rate",
    )
    @classmethod
    def validate_open_interval_metrics(cls, value: float) -> float:
        """Reject exact boundary grader metrics at the model boundary."""

        return safe_open_interval(value)


class FinanceAction(Action):
    """Action for categorizing transactions or finalizing the episode."""

    action_type: ActionType = Field(..., description="Requested environment action")
    transaction_id: Optional[str] = Field(
        default=None, description="Target transaction identifier"
    )
    category: Optional[CategoryName] = Field(
        default=None, description="Assigned category for categorize_transaction"
    )
    reason: Optional[str] = Field(
        default=None, description="Optional operator note explaining the action"
    )

    @model_validator(mode="after")
    def validate_action_shape(self) -> "FinanceAction":
        """Enforce the minimal action contract for the current milestone."""

        if self.action_type == ActionType.CATEGORIZE_TRANSACTION:
            if not self.transaction_id:
                raise ValueError(
                    "transaction_id is required for categorize_transaction actions"
                )
            if self.category is None:
                raise ValueError(
                    "category is required for categorize_transaction actions"
                )
        elif self.action_type == ActionType.FINALIZE:
            if self.category is not None:
                raise ValueError("category must not be provided for finalize actions")

        return self


class FinanceObservation(Observation):
    """Observation returned to the agent after reset and each step."""

    task_id: str = Field(..., description="Current task identifier")
    task_description: str = Field(..., description="Human-readable task objective")
    difficulty: DifficultyLevel = Field(..., description="Task difficulty level")
    allowed_actions: List[ActionType] = Field(
        default_factory=list, description="Actions currently supported by the env"
    )
    allowed_categories: List[CategoryName] = Field(
        default_factory=list, description="Categories available for classification"
    )
    unresolved_transactions: List[TransactionRecord] = Field(
        default_factory=list,
        description="Transactions that still need processing",
    )
    ledger_entries: List[LedgerEntry] = Field(
        default_factory=list, description="Processed ledger entries"
    )
    ledger_summary: LedgerSummary = Field(
        default_factory=LedgerSummary, description="Current processing summary"
    )
    action_history: List[ActionHistoryEntry] = Field(
        default_factory=list,
        description="Compact history of environment actions so far",
    )
    warnings: List[str] = Field(
        default_factory=list, description="Validation or workflow warnings"
    )
    current_transaction_id: Optional[str] = Field(
        default=None,
        description="Primary transaction to focus on next, if any remain",
    )
    step_budget_remaining: Optional[int] = Field(
        default=None, description="Remaining action budget for the task"
    )
    last_reward: Optional[FinanceReward] = Field(
        default=None, description="Structured reward details for the latest step"
    )


class TaskFixture(FinanceBaseModel):
    """Deterministic in-memory task definition used to initialize episodes."""

    task_id: str = Field(...)
    difficulty: DifficultyLevel = Field(...)
    task_description: str = Field(...)
    max_steps: int = Field(..., ge=1)
    transactions: List[TransactionRecord] = Field(default_factory=list)
    answer_key: Dict[str, CategoryName] = Field(default_factory=dict)


class FinanceState(State):
    """Public environment state returned by the environment API."""

    task_id: str = Field(..., description="Current task identifier")
    difficulty: DifficultyLevel = Field(..., description="Task difficulty level")
    task_description: str = Field(..., description="Goal statement for the episode")
    max_steps: int = Field(..., ge=1, description="Maximum steps for the episode")
    done: bool = Field(default=False, description="Whether the episode has ended")
    finalized: bool = Field(default=False, description="Whether finalize was called")
    transaction_queue: List[TransactionRecord] = Field(default_factory=list)
    processed_entries: Dict[str, LedgerEntry] = Field(default_factory=dict)
    allowed_categories: List[CategoryName] = Field(default_factory=list)
    allowed_actions: List[ActionType] = Field(default_factory=list)
    action_history: List[ActionHistoryEntry] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    invalid_action_count: int = Field(default=0, ge=0)
    cumulative_reward: float = Field(default=0.0)
    last_reward: Optional[FinanceReward] = Field(default=None)
