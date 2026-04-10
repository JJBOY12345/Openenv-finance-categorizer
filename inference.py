"""Submission-oriented baseline runner for the finance categorizer environment."""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import ValidationError

from finance_env.models import ActionType, CategoryName, FinanceAction, FinanceObservation, TransactionRecord
from finance_env.server.finance_env_environment import FinanceEnvironment


ENV_NAME = "finance_categorizer"
TASK_IDS = [
    "easy_budget_cleanup_v1",
    "medium_ambiguous_ledger_v1",
    "hard_operational_ledger_v1",
]
SYSTEM_PROMPT = (
    "You categorize personal finance transactions. "
    "Return exactly one compact JSON object and nothing else. "
    "Valid actions are categorize_transaction and finalize."
)
RAW_OUTPUT_PREVIEW_CHARS = 240
PRIMARY_FAILOVER_MODEL = "Qwen/Qwen2.5-7B-Instruct:fastest"
RETRYABLE_ERROR_TYPES = {"APIStatusError", "APITimeoutError", "APIConnectionError"}
MAX_API_STATUS_RETRIES = 2
RETRY_BACKOFF_SECONDS = 0.75


@dataclass
class BaselineConfig:
    """Runtime configuration for the baseline script."""

    api_base_url: str
    model_name: str
    hf_token: str
    request_timeout_s: float = 60.0


def load_config() -> BaselineConfig:
    """Load required environment variables and fail clearly if missing."""

    load_dotenv()
    api_base_url = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
    model_name = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct:fastest")
    hf_token = os.getenv("HF_TOKEN")

    if not hf_token:
        raise SystemExit("Missing required environment variable: HF_TOKEN must be set.")

    return BaselineConfig(
        api_base_url=api_base_url,
        model_name=model_name,
        hf_token=hf_token,
    )


def build_prompt(observation: FinanceObservation) -> str:
    """Build a compact prompt from public observation data only."""

    unresolved_lines = [
        (
            f"{transaction.transaction_id} | merchant={transaction.merchant} | "
            f"amount={transaction.amount:.2f} | memo={transaction.memo or '-'} | "
            f"channel={transaction.channel}"
        )
        for transaction in observation.unresolved_transactions
    ]

    recent_history = observation.action_history[-3:]
    history_lines = [
        (
            f"{entry.step_index}:{entry.action_type.value}:"
            f"{entry.transaction_id or '-'}:{entry.category.value if entry.category else '-'}"
        )
        for entry in recent_history
    ]

    prompt_lines = [
        f"task_id: {observation.task_id}",
        f"difficulty: {observation.difficulty.value}",
        f"task: {observation.task_description}",
        "allowed_actions: categorize_transaction, finalize",
        "allowed_categories: " + ",".join(
            category.value for category in observation.allowed_categories
        ),
        f"processed_count: {observation.ledger_summary.processed_count}",
        f"unresolved_count: {observation.ledger_summary.unresolved_count}",
        "recent_history:",
    ]
    prompt_lines.extend(history_lines or ["none"])
    prompt_lines.append("unresolved_transactions:")
    prompt_lines.extend(unresolved_lines or ["none"])
    prompt_lines.append(
        'Return exactly one compact JSON object like '
        '{"action_type":"categorize_transaction","transaction_id":"txn_001","category":"groceries"} '
        'or {"action_type":"finalize"}.'
    )
    return "\n".join(prompt_lines)


def request_model_action(
    client: OpenAI,
    model_name: str,
    observation: FinanceObservation,
    request_timeout_s: float,
) -> tuple[str | None, str | None]:
    """Ask the model for the next action with retry/failover on provider errors."""

    candidate_models = [model_name]
    if model_name == "Qwen/Qwen2.5-7B-Instruct:together":
        candidate_models.append(PRIMARY_FAILOVER_MODEL)

    last_error_label: str | None = None

    for model_index, candidate_model in enumerate(candidate_models):
        for attempt in range(MAX_API_STATUS_RETRIES + 1):
            try:
                response = client.chat.completions.create(
                    model=candidate_model,
                    temperature=0,
                    max_tokens=120,
                    timeout=request_timeout_s,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": build_prompt(observation)},
                    ],
                )
                content = response.choices[0].message.content
                return content, None
            except Exception as exc:  # pragma: no cover - depends on external endpoint
                error_type = type(exc).__name__
                last_error_label = f"model_error:{error_type}"
                is_retryable = error_type in RETRYABLE_ERROR_TYPES
                is_last_attempt = attempt >= MAX_API_STATUS_RETRIES

                if is_retryable and not is_last_attempt:
                    debug_log(
                        f"[DEBUG] task={observation.task_id} retry={attempt + 1} "
                        f"model={candidate_model} reason={last_error_label} "
                        f"backoff_s={RETRY_BACKOFF_SECONDS:.2f}"
                    )
                    time.sleep(RETRY_BACKOFF_SECONDS)
                    continue

                if is_retryable and model_index + 1 < len(candidate_models):
                    next_model = candidate_models[model_index + 1]
                    debug_log(
                        f"[DEBUG] task={observation.task_id} switch_model_from={candidate_model} "
                        f"switch_model_to={next_model} reason={last_error_label}"
                    )
                    break

                return None, last_error_label

    return None, last_error_label or "model_error:UnknownError"


def balanced_json_substring(text: str) -> str:
    """Return the first balanced JSON object substring found in text."""

    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in model output.")

    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]

    raise ValueError("Unterminated JSON object in model output.")


def extract_json_object(text: str) -> dict[str, Any]:
    """Extract a JSON object from raw model text."""

    stripped = text.strip()
    if stripped.startswith("```"):
        lines = [line for line in stripped.splitlines() if not line.startswith("```")]
        stripped = "\n".join(lines).strip()

    return json.loads(balanced_json_substring(stripped))


def parse_action(raw_text: str) -> FinanceAction:
    """Parse and validate model JSON into a typed action."""

    payload = extract_json_object(raw_text)
    return FinanceAction.model_validate(payload)


def preview_text(text: str | None) -> str:
    """Return a short single-line preview for stderr debug output."""

    if not text:
        return "<empty>"
    compact = " ".join(text.strip().split())
    if len(compact) <= RAW_OUTPUT_PREVIEW_CHARS:
        return compact
    return compact[:RAW_OUTPUT_PREVIEW_CHARS] + "..."


def heuristic_category(transaction: TransactionRecord) -> CategoryName:
    """Return a weak deterministic fallback category from public transaction data."""

    text = f"{transaction.merchant} {transaction.memo} {transaction.channel}".lower()

    generic_rules: list[tuple[list[str], CategoryName]] = [
        (["grocery", "supermarket", "market"], CategoryName.GROCERIES),
        (["restaurant", "cafe", "coffee", "lunch", "dinner"], CategoryName.DINING),
        (["transit", "metro", "uber", "ride", "taxi"], CategoryName.TRANSPORT),
        (["electric", "water", "utility", "internet", "gas bill"], CategoryName.UTILITIES),
        (["rent", "landlord", "lease"], CategoryName.RENT),
        (["subscription", "streaming", "storage", "membership", "monthly plan"], CategoryName.SUBSCRIPTIONS),
        (["pharmacy", "clinic", "doctor", "hospital", "prescription"], CategoryName.HEALTHCARE),
        (["marketplace", "store", "shop", "purchase", "retail"], CategoryName.SHOPPING),
        (["flight", "hotel", "airbnb", "travel"], CategoryName.TRAVEL),
        (["movie", "concert", "gaming", "entertainment"], CategoryName.ENTERTAINMENT),
        (["service charge", "fee", "overdraft", "bank fee"], CategoryName.FEES),
        (["salary", "payroll", "wages", "bonus"], CategoryName.INCOME),
    ]

    for needles, category in generic_rules:
        if any(needle in text for needle in needles):
            return category

    if transaction.amount > 0:
        return CategoryName.UNCATEGORIZED
    return CategoryName.UNCATEGORIZED


def fallback_action(observation: FinanceObservation) -> FinanceAction:
    """Return a safe non-oracular fallback action from public observation only."""

    if not observation.unresolved_transactions:
        return FinanceAction(action_type=ActionType.FINALIZE)

    transaction = observation.unresolved_transactions[0]
    return FinanceAction(
        action_type=ActionType.CATEGORIZE_TRANSACTION,
        transaction_id=transaction.transaction_id,
        category=heuristic_category(transaction),
        reason="deterministic_fallback",
    )


def debug_log(message: str) -> None:
    """Send debug output to stderr only."""

    print(message, file=sys.stderr)


def compact_action_string(action: FinanceAction) -> str:
    """Serialize an action as compact stable JSON for stdout."""

    return json.dumps(
        action.model_dump(mode="json", exclude_none=True, exclude_defaults=True),
        separators=(",", ":"),
        sort_keys=True,
    )


def format_reward(value: float | None) -> str:
    """Format rewards consistently for stdout."""

    if value is None:
        return "0.01"
    numeric = max(0.01, min(0.99, float(value)))
    return f"{numeric:.2f}"


def choose_action(
    client: OpenAI,
    model_name: str,
    observation: FinanceObservation,
    request_timeout_s: float,
    step_hint: int,
) -> tuple[FinanceAction, str]:
    """Choose the next action using the model first and fallback second."""

    raw_text, error_label = request_model_action(
        client,
        model_name,
        observation,
        request_timeout_s=request_timeout_s,
    )
    if raw_text is None:
        fallback = fallback_action(observation)
        debug_log(
            f"[DEBUG] task={observation.task_id} step={step_hint} "
            f"reason={error_label} fallback_action={compact_action_string(fallback)} raw_output=<empty>"
        )
        return fallback, error_label or "fallback"

    try:
        return parse_action(raw_text), "null"
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        fallback = fallback_action(observation)
        debug_log(
            f"[DEBUG] task={observation.task_id} step={step_hint} "
            f"reason=fallback_parse:{type(exc).__name__} "
            f"fallback_action={compact_action_string(fallback)} "
            f"raw_output={preview_text(raw_text)}"
        )
        return fallback, f"fallback_parse:{type(exc).__name__}"


def print_start(task_id: str, model_name: str) -> None:
    """Emit the required start line."""

    print(f"[START] task={task_id} env={ENV_NAME} model={model_name}")


def print_step(step_index: int, action: FinanceAction, reward: float | None, done: bool, error: str) -> None:
    """Emit one required step line."""

    print(
        f"[STEP] step={step_index} action={compact_action_string(action)} "
        f"reward={format_reward(reward)} done={str(done).lower()} error={error}"
    )


def print_end(success: bool, score: float, rewards: list[float | None]) -> None:
    """Emit the required end line."""

    reward_values = ",".join(format_reward(value) for value in rewards)
    print(
        f"[END] success={str(success).lower()} steps={len(rewards)} score={score:.4f} rewards={reward_values}"
    )


def run_task(
    client: OpenAI,
    model_name: str,
    task_id: str,
    request_timeout_s: float,
) -> None:
    """Run one task and emit only structured stdout lines."""

    env = FinanceEnvironment()
    observation = env.reset(task_id=task_id)
    rewards: list[float | None] = []

    print_start(task_id, model_name)

    try:
        while not observation.done and env.state.step_count < env.state.max_steps:
            action, error = choose_action(
                client,
                model_name,
                observation,
                request_timeout_s=request_timeout_s,
                step_hint=env.state.step_count + 1,
            )
            observation = env.step(action)
            rewards.append(observation.reward)
            print_step(
                env.state.step_count,
                action,
                observation.reward,
                observation.done,
                error,
            )

        if not env.state.done:
            action = FinanceAction(action_type=ActionType.FINALIZE)
            observation = env.step(action)
            rewards.append(observation.reward)
            print_step(
                env.state.step_count,
                action,
                observation.reward,
                observation.done,
                "forced_finalize",
            )

        score = env.grade_episode().score
        print_end(True, score, rewards)
    except Exception as exc:  # pragma: no cover - defensive baseline safeguard
        debug_log(f"[DEBUG] task={task_id} fatal_error={type(exc).__name__}:{exc}")
        try:
            score = env.grade_episode().score
        except Exception:
            score = 0.01
        print_end(False, score, rewards)


def main() -> None:
    """Run the baseline across all implemented tasks."""

    config = load_config()
    client = OpenAI(base_url=config.api_base_url, api_key=config.hf_token)
    for task_id in TASK_IDS:
        run_task(client, config.model_name, task_id, config.request_timeout_s)


if __name__ == "__main__":
    main()
