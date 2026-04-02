from finance_env.models import ActionType, CategoryName, FinanceAction
from finance_env.server.finance_env_environment import FinanceEnvironment


def test_reset_returns_valid_initial_observation():
    env = FinanceEnvironment()

    observation = env.reset()

    assert observation.done is False
    assert observation.task_id == "easy_budget_cleanup_v1"
    assert observation.ledger_summary.processed_count == 0
    assert observation.ledger_summary.unresolved_count == 5
    assert observation.current_transaction_id == "txn_001"
    assert observation.reward is None


def test_valid_categorization_updates_state_and_reward():
    env = FinanceEnvironment()
    env.reset()

    observation = env.step(
        FinanceAction(
            action_type=ActionType.CATEGORIZE_TRANSACTION,
            transaction_id="txn_001",
            category=CategoryName.GROCERIES,
        )
    )

    assert observation.reward == 0.24
    assert observation.ledger_summary.processed_count == 1
    assert observation.ledger_summary.unresolved_count == 4
    assert env.state.processed_entries["txn_001"].assigned_category == CategoryName.GROCERIES


def test_invalid_transaction_gets_penalty_and_warning():
    env = FinanceEnvironment()
    env.reset()

    observation = env.step(
        FinanceAction(
            action_type=ActionType.CATEGORIZE_TRANSACTION,
            transaction_id="missing_txn",
            category=CategoryName.GROCERIES,
        )
    )

    assert observation.reward == -0.51
    assert observation.warnings == ["Unknown transaction id: missing_txn."]
    assert env.state.invalid_action_count == 1
    assert observation.ledger_summary.processed_count == 0


def test_finalize_before_completion_ends_episode_with_penalty():
    env = FinanceEnvironment()
    env.reset()

    observation = env.step(FinanceAction(action_type=ActionType.FINALIZE))

    assert observation.done is True
    assert observation.reward == -0.21
    assert "Finalize called before all transactions were processed." in observation.warnings
    assert env.state.finalized is True


def test_public_state_and_observation_do_not_expose_answer_key():
    env = FinanceEnvironment()
    env.reset()
    observation = env.step(
        FinanceAction(
            action_type=ActionType.CATEGORIZE_TRANSACTION,
            transaction_id="txn_001",
            category=CategoryName.GROCERIES,
        )
    )

    state_dump = env.state.model_dump()
    observation_dump = observation.model_dump()

    assert "answer_key" not in state_dump
    assert "answer_key" not in observation_dump
    assert "is_correct" not in state_dump["processed_entries"]["txn_001"]
    assert "is_correct" not in observation_dump["ledger_entries"][0]


def test_wrong_categorization_does_not_leak_expected_label():
    env = FinanceEnvironment()
    env.reset()

    observation = env.step(
        FinanceAction(
            action_type=ActionType.CATEGORIZE_TRANSACTION,
            transaction_id="txn_002",
            category=CategoryName.GROCERIES,
        )
    )

    assert observation.reward == -0.21
    assert "utilities" not in observation.last_reward.reason.lower()
    assert "utilities" not in observation.action_history[-1].outcome.lower()


def test_easy_grader_rewards_correct_complete_run():
    env = FinanceEnvironment()
    env.reset()

    actions = [
        ("txn_001", CategoryName.GROCERIES),
        ("txn_002", CategoryName.UTILITIES),
        ("txn_003", CategoryName.TRANSPORT),
        ("txn_004", CategoryName.SUBSCRIPTIONS),
        ("txn_005", CategoryName.INCOME),
    ]
    for transaction_id, category in actions:
        env.step(
            FinanceAction(
                action_type=ActionType.CATEGORIZE_TRANSACTION,
                transaction_id=transaction_id,
                category=category,
            )
        )
    env.step(FinanceAction(action_type=ActionType.FINALIZE))

    result = env.grade_episode()

    assert result.score == 1.0
    assert result.categorized_accuracy == 1.0
    assert result.completion_ratio == 1.0
    assert result.premature_finalize is False


def test_easy_grader_penalizes_wrong_labels_and_premature_finalize():
    env = FinanceEnvironment()
    env.reset()

    env.step(
        FinanceAction(
            action_type=ActionType.CATEGORIZE_TRANSACTION,
            transaction_id="txn_001",
            category=CategoryName.DINING,
        )
    )
    env.step(FinanceAction(action_type=ActionType.FINALIZE))

    result = env.grade_episode()

    assert 0.0 <= result.score <= 1.0
    assert result.score < 0.5
    assert result.categorized_accuracy == 0.0
    assert result.completion_ratio == 0.2
    assert result.premature_finalize is True


def test_medium_task_reset_selects_ambiguous_fixture_without_leaking_answers():
    env = FinanceEnvironment()

    observation = env.reset(task_id="medium_ambiguous_ledger_v1")
    state_dump = env.state.model_dump()
    observation_dump = observation.model_dump()

    assert observation.task_id == "medium_ambiguous_ledger_v1"
    assert observation.difficulty.value == "medium"
    assert observation.ledger_summary.unresolved_count == 5
    assert observation.current_transaction_id == "txn_m001"
    assert "answer_key" not in state_dump
    assert "answer_key" not in observation_dump


def test_medium_grader_rewards_correct_complete_run():
    env = FinanceEnvironment()
    env.reset(task_id="medium_ambiguous_ledger_v1")

    actions = [
        ("txn_m001", CategoryName.SUBSCRIPTIONS),
        ("txn_m002", CategoryName.TRANSFER),
        ("txn_m003", CategoryName.HEALTHCARE),
        ("txn_m004", CategoryName.SHOPPING),
        ("txn_m005", CategoryName.TRANSPORT),
    ]
    for transaction_id, category in actions:
        env.step(
            FinanceAction(
                action_type=ActionType.CATEGORIZE_TRANSACTION,
                transaction_id=transaction_id,
                category=category,
            )
        )
    env.step(FinanceAction(action_type=ActionType.FINALIZE))

    result = env.grade_episode()

    assert result.score == 1.0
    assert result.categorized_accuracy == 1.0
    assert result.completion_ratio == 1.0
    assert result.premature_finalize is False


def test_medium_grader_penalizes_transfer_confusion_and_early_finalize():
    env = FinanceEnvironment()
    env.reset(task_id="medium_ambiguous_ledger_v1")

    env.step(
        FinanceAction(
            action_type=ActionType.CATEGORIZE_TRANSACTION,
            transaction_id="txn_m002",
            category=CategoryName.INCOME,
        )
    )
    env.step(FinanceAction(action_type=ActionType.FINALIZE))

    result = env.grade_episode()

    assert 0.0 <= result.score <= 1.0
    assert result.score < 0.5
    assert result.categorized_accuracy == 0.0
    assert result.completion_ratio == 0.2
    assert result.premature_finalize is True


def test_hard_task_reset_selects_fixture_without_leaking_answers():
    env = FinanceEnvironment()

    observation = env.reset(task_id="hard_operational_ledger_v1")
    state_dump = env.state.model_dump()
    observation_dump = observation.model_dump()

    assert observation.task_id == "hard_operational_ledger_v1"
    assert observation.difficulty.value == "hard"
    assert observation.ledger_summary.unresolved_count == 8
    assert observation.current_transaction_id == "txn_h001"
    assert "answer_key" not in state_dump
    assert "answer_key" not in observation_dump


def test_hard_grader_rewards_correct_complete_run():
    env = FinanceEnvironment()
    env.reset(task_id="hard_operational_ledger_v1")

    actions = [
        ("txn_h001", CategoryName.SUBSCRIPTIONS),
        ("txn_h002", CategoryName.SHOPPING),
        ("txn_h003", CategoryName.TRANSFER),
        ("txn_h004", CategoryName.TRANSFER),
        ("txn_h005", CategoryName.TRANSFER),
        ("txn_h006", CategoryName.FEES),
        ("txn_h007", CategoryName.DINING),
        ("txn_h008", CategoryName.HEALTHCARE),
    ]
    for transaction_id, category in actions:
        env.step(
            FinanceAction(
                action_type=ActionType.CATEGORIZE_TRANSACTION,
                transaction_id=transaction_id,
                category=category,
            )
        )
    env.step(FinanceAction(action_type=ActionType.FINALIZE))

    result = env.grade_episode()

    assert result.score == 1.0
    assert result.categorized_accuracy == 1.0
    assert result.completion_ratio == 1.0
    assert result.premature_finalize is False


def test_hard_grader_penalizes_wrong_categorization():
    env = FinanceEnvironment()
    env.reset(task_id="hard_operational_ledger_v1")

    env.step(
        FinanceAction(
            action_type=ActionType.CATEGORIZE_TRANSACTION,
            transaction_id="txn_h006",
            category=CategoryName.UTILITIES,
        )
    )
    env.step(
        FinanceAction(
            action_type=ActionType.CATEGORIZE_TRANSACTION,
            transaction_id="txn_h007",
            category=CategoryName.DINING,
        )
    )
    env.step(FinanceAction(action_type=ActionType.FINALIZE))

    result = env.grade_episode()

    assert 0.0 <= result.score <= 1.0
    assert result.score < 0.5
    assert result.categorized_accuracy == 0.5
    assert result.completion_ratio == 0.25
    assert result.premature_finalize is True


def test_hard_grader_penalizes_premature_finalize():
    env = FinanceEnvironment()
    env.reset(task_id="hard_operational_ledger_v1")

    env.step(FinanceAction(action_type=ActionType.FINALIZE))

    result = env.grade_episode()

    assert 0.0 <= result.score <= 1.0
    assert result.score == 0.0
    assert result.categorized_accuracy == 0.0
    assert result.completion_ratio == 0.0
    assert result.premature_finalize is True
