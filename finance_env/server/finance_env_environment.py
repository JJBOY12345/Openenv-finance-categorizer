# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Finance categorization environment implementation.

This first pass supports a single deterministic easy task where the agent
assigns one category per transaction and finalizes the ledger.
"""

from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment

try:
    from ..grading import grade_easy_task, grade_hard_task, grade_medium_task
    from ..models import (
        ActionHistoryEntry,
        ActionType,
        CategoryName,
        DifficultyLevel,
        FinanceAction,
        FinanceGraderResult,
        FinanceObservation,
        FinanceReward,
        FinanceState,
        LedgerEntry,
        LedgerSummary,
        RewardBreakdown,
        TaskFixture,
        TransactionRecord,
        safe_open_interval,
    )
except ImportError:
    from grading import grade_easy_task, grade_hard_task, grade_medium_task
    from models import (
        ActionHistoryEntry,
        ActionType,
        CategoryName,
        DifficultyLevel,
        FinanceAction,
        FinanceGraderResult,
        FinanceObservation,
        FinanceReward,
        FinanceState,
        LedgerEntry,
        LedgerSummary,
        RewardBreakdown,
        TaskFixture,
        TransactionRecord,
        safe_open_interval,
    )


ALLOWED_CATEGORIES = [category for category in CategoryName]
ALLOWED_ACTIONS = [ActionType.CATEGORIZE_TRANSACTION, ActionType.FINALIZE]

EASY_TASK_FIXTURE = TaskFixture(
    task_id="easy_budget_cleanup_v1",
    difficulty=DifficultyLevel.EASY,
    task_description=(
        "Categorize each everyday consumer transaction into the correct budget "
        "category and finalize the ledger when all transactions are processed."
    ),
    max_steps=10,
    transactions=[
        TransactionRecord(
            transaction_id="txn_001",
            merchant="FreshMart Supermarket",
            amount=-86.42,
            currency="USD",
            posted_date="2026-03-01",
            memo="Weekly grocery run",
            channel="debit_card",
        ),
        TransactionRecord(
            transaction_id="txn_002",
            merchant="City Electric Utility",
            amount=-124.18,
            currency="USD",
            posted_date="2026-03-02",
            memo="Monthly electric bill",
            channel="bank_transfer",
        ),
        TransactionRecord(
            transaction_id="txn_003",
            merchant="Metro Transit Reload",
            amount=-25.00,
            currency="USD",
            posted_date="2026-03-03",
            memo="Transit card reload",
            channel="card",
        ),
        TransactionRecord(
            transaction_id="txn_004",
            merchant="StreamFlix",
            amount=-15.99,
            currency="USD",
            posted_date="2026-03-04",
            memo="Monthly streaming plan",
            channel="card",
        ),
        TransactionRecord(
            transaction_id="txn_005",
            merchant="ACME Payroll",
            amount=2350.00,
            currency="USD",
            posted_date="2026-03-05",
            memo="Biweekly paycheck",
            channel="ach",
        ),
    ],
    answer_key={
        "txn_001": CategoryName.GROCERIES,
        "txn_002": CategoryName.UTILITIES,
        "txn_003": CategoryName.TRANSPORT,
        "txn_004": CategoryName.SUBSCRIPTIONS,
        "txn_005": CategoryName.INCOME,
    },
)

MEDIUM_TASK_FIXTURE = TaskFixture(
    task_id="medium_ambiguous_ledger_v1",
    difficulty=DifficultyLevel.MEDIUM,
    task_description=(
        "Categorize a realistic ledger with ambiguous merchants and transfer-versus-"
        "expense confusion, then finalize the ledger when complete."
    ),
    max_steps=12,
    transactions=[
        TransactionRecord(
            transaction_id="txn_m001",
            merchant="APPLE.COM/BILL",
            amount=-10.99,
            currency="USD",
            posted_date="2026-03-08",
            memo="iCloud+ 2TB monthly plan",
            channel="card",
        ),
        TransactionRecord(
            transaction_id="txn_m002",
            merchant="Zelle",
            amount=120.00,
            currency="USD",
            posted_date="2026-03-09",
            memo="Transfer from Alex for shared utilities",
            channel="ach",
        ),
        TransactionRecord(
            transaction_id="txn_m003",
            merchant="CVS Pharmacy",
            amount=-27.45,
            currency="USD",
            posted_date="2026-03-10",
            memo="Prescription pickup",
            channel="card",
        ),
        TransactionRecord(
            transaction_id="txn_m004",
            merchant="AMZN Mktp US",
            amount=-42.13,
            currency="USD",
            posted_date="2026-03-11",
            memo="Household organizer and charging cable",
            channel="card",
        ),
        TransactionRecord(
            transaction_id="txn_m005",
            merchant="Uber",
            amount=-18.72,
            currency="USD",
            posted_date="2026-03-12",
            memo="Ride to downtown office",
            channel="card",
        ),
    ],
    answer_key={
        "txn_m001": CategoryName.SUBSCRIPTIONS,
        "txn_m002": CategoryName.TRANSFER,
        "txn_m003": CategoryName.HEALTHCARE,
        "txn_m004": CategoryName.SHOPPING,
        "txn_m005": CategoryName.TRANSPORT,
    },
)

HARD_TASK_FIXTURE = TaskFixture(
    task_id="hard_operational_ledger_v1",
    difficulty=DifficultyLevel.HARD,
    task_description=(
        "Categorize a challenging operational ledger with ambiguous merchants, "
        "transfer-versus-income confusion, fee classification, and similar merchant "
        "names that require careful reading of memo and channel details."
    ),
    max_steps=14,
    transactions=[
        TransactionRecord(
            transaction_id="txn_h001",
            merchant="APPLE.COM/BILL",
            amount=-10.99,
            currency="USD",
            posted_date="2026-03-14",
            memo="iCloud+ monthly storage",
            channel="card",
        ),
        TransactionRecord(
            transaction_id="txn_h002",
            merchant="APPLE FIFTH AVE",
            amount=-1299.00,
            currency="USD",
            posted_date="2026-03-15",
            memo="MacBook purchase",
            channel="card",
        ),
        TransactionRecord(
            transaction_id="txn_h003",
            merchant="PAYPAL TRANSFER",
            amount=250.00,
            currency="USD",
            posted_date="2026-03-16",
            memo="Move money from PayPal balance",
            channel="ach",
        ),
        TransactionRecord(
            transaction_id="txn_h004",
            merchant="PAYPAL *JONMARTIN",
            amount=75.00,
            currency="USD",
            posted_date="2026-03-16",
            memo="Birthday reimbursement from Jon",
            channel="ach",
        ),
        TransactionRecord(
            transaction_id="txn_h005",
            merchant="VENMO CASHOUT",
            amount=-300.00,
            currency="USD",
            posted_date="2026-03-17",
            memo="Transfer to checking",
            channel="ach",
        ),
        TransactionRecord(
            transaction_id="txn_h006",
            merchant="BANK OF METRO",
            amount=-35.00,
            currency="USD",
            posted_date="2026-03-18",
            memo="Monthly service charge",
            channel="bank_fee",
        ),
        TransactionRecord(
            transaction_id="txn_h007",
            merchant="SQ *NORA CAFE",
            amount=-14.80,
            currency="USD",
            posted_date="2026-03-18",
            memo="Lunch meeting",
            channel="card",
        ),
        TransactionRecord(
            transaction_id="txn_h008",
            merchant="SQ *NORA STUDIO",
            amount=-48.00,
            currency="USD",
            posted_date="2026-03-19",
            memo="Yoga class pack",
            channel="card",
        ),
    ],
    answer_key={
        "txn_h001": CategoryName.SUBSCRIPTIONS,
        "txn_h002": CategoryName.SHOPPING,
        "txn_h003": CategoryName.TRANSFER,
        "txn_h004": CategoryName.TRANSFER,
        "txn_h005": CategoryName.TRANSFER,
        "txn_h006": CategoryName.FEES,
        "txn_h007": CategoryName.DINING,
        "txn_h008": CategoryName.HEALTHCARE,
    },
)

TASK_FIXTURES = {
    EASY_TASK_FIXTURE.task_id: EASY_TASK_FIXTURE,
    MEDIUM_TASK_FIXTURE.task_id: MEDIUM_TASK_FIXTURE,
    HARD_TASK_FIXTURE.task_id: HARD_TASK_FIXTURE,
}


@dataclass
class _EpisodeSecrets:
    """Private grading data that must not be exposed through public state."""

    answer_key: dict[str, CategoryName]


class FinanceEnvironment(Environment):
    """Deterministic finance categorization environment."""

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        super().__init__()
        self._fixture = EASY_TASK_FIXTURE
        self._episode_secrets = _EpisodeSecrets(
            answer_key=deepcopy(self._fixture.answer_key)
        )
        self._state = self._build_state(episode_id=str(uuid4()))

    def reset(
        self,
        seed: int | None = None,
        episode_id: str | None = None,
        **kwargs,
    ) -> FinanceObservation:
        """Reset the environment to the requested deterministic task."""

        del seed
        requested_task_id = kwargs.pop("task_id", self._fixture.task_id)
        self._fixture = self._resolve_fixture(requested_task_id)
        self._state = self._build_state(episode_id=episode_id or str(uuid4()))
        return self._build_observation(
            warnings=[],
            reward_detail=None,
        )

    def step(
        self,
        action: FinanceAction,
        timeout_s: float | None = None,
        **kwargs,
    ) -> FinanceObservation:
        """Process a categorization or finalize action."""

        del timeout_s, kwargs

        if self._state.done:
            return self._invalid_action_observation(
                "Episode already finalized; reset the environment to start again."
            )

        self._state.step_count += 1
        self._state.warnings = []

        if action.action_type == ActionType.CATEGORIZE_TRANSACTION:
            reward_detail, warning = self._handle_categorize(action)
        elif action.action_type == ActionType.FINALIZE:
            reward_detail, warning = self._handle_finalize(action)
        else:
            reward_detail = self._make_reward(
                invalid_action_penalty=-0.5,
                step_penalty=-0.01,
                reason=f"Unsupported action type: {action.action_type}.",
            )
            warning = f"Unsupported action type: {action.action_type}."
            self._state.invalid_action_count += 1

        if warning:
            self._state.warnings = [warning]

        self._state.last_reward = reward_detail
        self._state.cumulative_reward += reward_detail.value

        return self._build_observation(
            warnings=self._state.warnings,
            reward_detail=reward_detail,
        )

    @property
    def state(self) -> FinanceState:
        """Return the public environment state without hidden answer data."""

        return self._state

    def grade_episode(self) -> FinanceGraderResult:
        """Grade the current episode deterministically based on the active task."""
        grader = {
            EASY_TASK_FIXTURE.task_id: grade_easy_task,
            MEDIUM_TASK_FIXTURE.task_id: grade_medium_task,
            HARD_TASK_FIXTURE.task_id: grade_hard_task,
        }.get(self._state.task_id, grade_easy_task)
        return grader(
            state=self._state,
            answer_key=self._episode_secrets.answer_key,
        )

    def _handle_categorize(
        self, action: FinanceAction
    ) -> tuple[FinanceReward, str | None]:
        transaction = self._find_transaction(action.transaction_id)
        if transaction is None:
            self._state.invalid_action_count += 1
            return (
                self._make_reward(
                    invalid_action_penalty=-0.5,
                    step_penalty=-0.01,
                    reason=f"Unknown transaction id: {action.transaction_id}.",
                ),
                f"Unknown transaction id: {action.transaction_id}.",
            )

        if action.transaction_id in self._state.processed_entries:
            self._state.invalid_action_count += 1
            return (
                self._make_reward(
                    invalid_action_penalty=-0.4,
                    step_penalty=-0.01,
                    reason=f"Transaction {action.transaction_id} is already categorized.",
                ),
                f"Transaction {action.transaction_id} is already categorized.",
            )

        assert action.category is not None
        correct_category = self._episode_secrets.answer_key[action.transaction_id]
        is_correct = action.category == correct_category

        entry = LedgerEntry(
            transaction_id=transaction.transaction_id,
            assigned_category=action.category,
            amount=transaction.amount,
            merchant=transaction.merchant,
            note=action.reason,
        )
        self._state.processed_entries[action.transaction_id] = entry

        outcome = (
            f"Categorized {action.transaction_id} as {action.category.value}."
            if is_correct
            else (
                f"Categorized {action.transaction_id} as {action.category.value}, "
                "but it was not accepted as correct."
            )
        )
        self._append_history(
            action_type=action.action_type,
            transaction_id=action.transaction_id,
            category=action.category,
            outcome=outcome,
        )

        if is_correct:
            return (
                self._make_reward(
                    correctness_reward=0.25,
                    step_penalty=-0.01,
                    reason=f"Correctly categorized {action.transaction_id}.",
                ),
                None,
            )

        return (
            self._make_reward(
                correctness_reward=-0.2,
                step_penalty=-0.01,
                reason=f"Incorrect category for {action.transaction_id}.",
            ),
            None,
        )

    def _handle_finalize(self, action: FinanceAction) -> tuple[FinanceReward, str | None]:
        del action

        unresolved_count = self._unresolved_count()
        correct_count = self._correct_count()
        total_transactions = len(self._state.transaction_queue)
        completion_ratio = correct_count / total_transactions if total_transactions else 0.0

        finalize_bonus = round(completion_ratio * 0.5, 4)
        premature_penalty = -0.2 if unresolved_count > 0 else 0.0
        reason = "Episode finalized."

        if unresolved_count > 0:
            reason = (
                "Episode finalized with unresolved transactions; completion score reduced."
            )

        self._append_history(
            action_type=ActionType.FINALIZE,
            transaction_id=None,
            category=None,
            outcome=reason,
        )
        self._state.finalized = True
        self._state.done = True

        return (
            self._make_reward(
                finalize_bonus=finalize_bonus,
                premature_finalize_penalty=premature_penalty,
                step_penalty=-0.01,
                reason=reason,
            ),
            None if unresolved_count == 0 else "Finalize called before all transactions were processed.",
        )

    def _invalid_action_observation(self, warning: str) -> FinanceObservation:
        self._state.invalid_action_count += 1
        self._state.step_count += 1
        reward_detail = self._make_reward(
            invalid_action_penalty=-0.5,
            step_penalty=-0.01,
            reason=warning,
        )
        self._state.last_reward = reward_detail
        self._state.cumulative_reward += reward_detail.value
        self._state.warnings = [warning]
        return self._build_observation(
            warnings=self._state.warnings,
            reward_detail=reward_detail,
        )

    def _build_state(self, episode_id: str) -> FinanceState:
        fixture = deepcopy(self._fixture)
        self._episode_secrets = _EpisodeSecrets(answer_key=deepcopy(fixture.answer_key))
        return FinanceState(
            episode_id=episode_id,
            step_count=0,
            task_id=fixture.task_id,
            difficulty=fixture.difficulty,
            task_description=fixture.task_description,
            max_steps=fixture.max_steps,
            done=False,
            finalized=False,
            transaction_queue=fixture.transactions,
            processed_entries={},
            allowed_categories=ALLOWED_CATEGORIES,
            allowed_actions=ALLOWED_ACTIONS,
            action_history=[],
            warnings=[],
            invalid_action_count=0,
            cumulative_reward=0.0,
            last_reward=None,
        )

    def _build_observation(
        self,
        warnings: list[str],
        reward_detail: FinanceReward | None,
    ) -> FinanceObservation:
        unresolved_transactions = [
            transaction
            for transaction in self._state.transaction_queue
            if transaction.transaction_id not in self._state.processed_entries
        ]
        current_transaction_id = (
            unresolved_transactions[0].transaction_id if unresolved_transactions else None
        )
        ledger_entries = list(self._state.processed_entries.values())
        ledger_summary = self._build_ledger_summary(unresolved_transactions)

        metadata = {
            "invalid_action_count": self._state.invalid_action_count,
            "cumulative_reward": round(self._state.cumulative_reward, 4),
            "processed_transaction_ids": list(self._state.processed_entries.keys()),
        }
        if reward_detail is not None:
            metadata["reward_breakdown"] = reward_detail.breakdown.model_dump(mode="json")

        return FinanceObservation(
            task_id=self._state.task_id,
            task_description=self._state.task_description,
            difficulty=self._state.difficulty,
            allowed_actions=self._state.allowed_actions,
            allowed_categories=self._state.allowed_categories,
            unresolved_transactions=unresolved_transactions,
            ledger_entries=ledger_entries,
            ledger_summary=ledger_summary,
            action_history=self._state.action_history,
            warnings=warnings,
            current_transaction_id=current_transaction_id,
            step_budget_remaining=max(self._state.max_steps - self._state.step_count, 0),
            last_reward=reward_detail,
            done=self._state.done,
            reward=None if reward_detail is None else reward_detail.value,
            metadata=metadata,
        )

    def _build_ledger_summary(
        self, unresolved_transactions: list[TransactionRecord]
    ) -> LedgerSummary:
        category_counts: dict[CategoryName, int] = {}

        for entry in self._state.processed_entries.values():
            category_counts[entry.assigned_category] = (
                category_counts.get(entry.assigned_category, 0) + 1
            )

        return LedgerSummary(
            processed_count=len(self._state.processed_entries),
            unresolved_count=len(unresolved_transactions),
            category_counts=category_counts,
        )

    def _append_history(
        self,
        action_type: ActionType,
        transaction_id: str | None,
        category: CategoryName | None,
        outcome: str,
    ) -> None:
        self._state.action_history.append(
            ActionHistoryEntry(
                step_index=self._state.step_count,
                action_type=action_type,
                transaction_id=transaction_id,
                category=category,
                outcome=outcome,
            )
        )

    def _find_transaction(self, transaction_id: str | None) -> TransactionRecord | None:
        if transaction_id is None:
            return None
        for transaction in self._state.transaction_queue:
            if transaction.transaction_id == transaction_id:
                return transaction
        return None

    def _resolve_fixture(self, task_id: str) -> TaskFixture:
        fixture = TASK_FIXTURES.get(task_id)
        if fixture is None:
            available = ", ".join(sorted(TASK_FIXTURES))
            raise ValueError(f"Unknown task_id '{task_id}'. Available task_ids: {available}")
        return fixture

    def _unresolved_count(self) -> int:
        return len(self._state.transaction_queue) - len(self._state.processed_entries)

    def _correct_count(self) -> int:
        return sum(
            1
            for transaction_id, entry in self._state.processed_entries.items()
            if self._episode_secrets.answer_key.get(transaction_id) == entry.assigned_category
        )

    def _make_reward(
        self,
        correctness_reward: float = 0.0,
        invalid_action_penalty: float = 0.0,
        finalize_bonus: float = 0.0,
        premature_finalize_penalty: float = 0.0,
        step_penalty: float = 0.0,
        reason: str = "",
    ) -> FinanceReward:
        breakdown = RewardBreakdown(
            correctness_reward=correctness_reward,
            invalid_action_penalty=invalid_action_penalty,
            finalize_bonus=finalize_bonus,
            premature_finalize_penalty=premature_finalize_penalty,
            step_penalty=step_penalty,
        )
        total = round(
            correctness_reward
            + invalid_action_penalty
            + finalize_bonus
            + premature_finalize_penalty
            + step_penalty,
            4,
        )
        total = safe_open_interval(total)
        return FinanceReward(value=total, breakdown=breakdown, reason=reason)


if __name__ == "__main__":  # pragma: no cover
    env = FinanceEnvironment()
    initial = env.reset()
    print(initial.model_dump_json(indent=2))
