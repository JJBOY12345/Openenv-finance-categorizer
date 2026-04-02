"""Lightweight baseline inference runner for the finance categorizer environment."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import ValidationError

from finance_env.models import ActionType, CategoryName, FinanceAction, FinanceObservation, TransactionRecord
from finance_env.server.finance_env_environment import FinanceEnvironment


TASK_IDS = [
    "easy_budget_cleanup_v1",
    "medium_ambiguous_ledger_v1",
    "hard_operational_ledger_v1",
]

SYSTEM_PROMPT = (
    "You are categorizing personal finance transactions. "
    "Return exactly one JSON object and nothing else. "
    "Valid actions are categorize_transaction and finalize."
)
RAW_OUTPUT_PREVIEW_CHARS = 240


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
    required = {
        "API_BASE_URL": os.getenv("API_BASE_URL"),
        "MODEL_NAME": os.getenv("MODEL_NAME"),
        "HF_TOKEN": os.getenv("HF_TOKEN"),
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise SystemExit(
            "Missing required environment variables: "
            + ", ".join(missing)
            + ". Set API_BASE_URL, MODEL_NAME, and HF_TOKEN before running inference.py."
        )

    return BaselineConfig(
        api_base_url=required["API_BASE_URL"] or "",
        model_name=required["MODEL_NAME"] or "",
        hf_token=required["HF_TOKEN"] or "",
    )


def build_prompt(observation: FinanceObservation) -> str:
    """Build a compact deterministic prompt from the current observation."""

    unresolved_lines = []
    for transaction in observation.unresolved_transactions:
        unresolved_lines.append(
            (
                f"{transaction.transaction_id} | merchant={transaction.merchant} | "
                f"amount={transaction.amount:.2f} | memo={transaction.memo or '-'} | "
                f"channel={transaction.channel}"
            )
        )

    recent_history = observation.action_history[-3:]
    history_lines = [
        (
            f"{entry.step_index}:{entry.action_type.value}:"
            f"{entry.transaction_id or '-'}:{entry.category.value if entry.category else '-'}:"
            f"{entry.outcome}"
        )
        for entry in recent_history
    ]

    prompt_lines = [
        f"task_id: {observation.task_id}",
        f"difficulty: {observation.difficulty.value}",
        f"task: {observation.task_description}",
        "allowed_actions: categorize_transaction, finalize",
        "allowed_categories: "
        + ", ".join(category.value for category in observation.allowed_categories),
        f"processed_count: {observation.ledger_summary.processed_count}",
        f"unresolved_count: {observation.ledger_summary.unresolved_count}",
        "recent_history:",
    ]
    prompt_lines.extend(history_lines or ["none"])
    prompt_lines.append("unresolved_transactions:")
    prompt_lines.extend(unresolved_lines or ["none"])
    prompt_lines.append(
        "Return exactly one JSON object with either "
        '{"action_type":"categorize_transaction","transaction_id":"...","category":"..."} '
        'or {"action_type":"finalize"}.'
    )
    return "\n".join(prompt_lines)


def request_model_action(
    client: OpenAI,
    model_name: str,
    observation: FinanceObservation,
    request_timeout_s: float,
) -> tuple[str | None, str | None]:
    """Ask the model for the next action and return raw content or an error label."""

    try:
        response = client.chat.completions.create(
            model=model_name,
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
        return None, f"model_error:{type(exc).__name__}"


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


def heuristic_category(transaction: TransactionRecord) -> CategoryName:
    """Deterministic conservative fallback when model output is unusable."""

    text = (
        f"{transaction.merchant} {transaction.memo} {transaction.channel}"
    ).lower()

    rules: list[tuple[list[str], CategoryName]] = [
        (["freshmart", "supermarket", "grocery"], CategoryName.GROCERIES),
        (["electric utility", "electric bill", "utility"], CategoryName.UTILITIES),
        (["transit", "metro", "uber", "ride"], CategoryName.TRANSPORT),
        (["streamflix", "icloud", "apple.com/bill", "monthly storage", "cloud"], CategoryName.SUBSCRIPTIONS),
        (["payroll", "salary", "paycheck"], CategoryName.INCOME),
        (["zelle", "paypal transfer", "venmo cashout", "transfer to checking", "reimbursement", "move money"], CategoryName.TRANSFER),
        (["cvs pharmacy", "prescription", "yoga", "studio"], CategoryName.HEALTHCARE),
        (["amzn", "apple fifth ave", "macbook", "purchase"], CategoryName.SHOPPING),
        (["service charge", "bank_fee", "bank of metro"], CategoryName.FEES),
        (["cafe", "lunch", "restaurant"], CategoryName.DINING),
    ]

    for needles, category in rules:
        if any(needle in text for needle in needles):
            return category

    if transaction.amount > 0:
        return CategoryName.TRANSFER
    return CategoryName.UNCATEGORIZED


def fallback_action(observation: FinanceObservation) -> FinanceAction:
    """Return a safe deterministic action when the model response is malformed."""

    if not observation.unresolved_transactions:
        return FinanceAction(action_type=ActionType.FINALIZE)

    transaction = observation.unresolved_transactions[0]
    return FinanceAction(
        action_type=ActionType.CATEGORIZE_TRANSACTION,
        transaction_id=transaction.transaction_id,
        category=heuristic_category(transaction),
        reason="deterministic_fallback",
    )


def preview_text(text: str | None) -> str:
    """Return a short single-line preview for debug output."""

    if not text:
        return "<empty>"
    compact = " ".join(text.strip().split())
    if len(compact) <= RAW_OUTPUT_PREVIEW_CHARS:
        return compact
    return compact[:RAW_OUTPUT_PREVIEW_CHARS] + "..."


def choose_action(
    client: OpenAI,
    model_name: str,
    observation: FinanceObservation,
    request_timeout_s: float,
) -> tuple[FinanceAction, str, str | None]:
    """Choose the next action using the model first and fallback second."""

    raw_text, error_label = request_model_action(
        client,
        model_name,
        observation,
        request_timeout_s=request_timeout_s,
    )
    if raw_text is None:
        return fallback_action(observation), error_label or "fallback", None

    try:
        return parse_action(raw_text), "model", raw_text
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        return fallback_action(observation), f"fallback_parse:{type(exc).__name__}", raw_text


def run_task(
    client: OpenAI,
    model_name: str,
    task_id: str,
    request_timeout_s: float,
) -> dict[str, Any]:
    """Run one episode for a given task and return a compact summary."""

    env = FinanceEnvironment()
    observation = env.reset(task_id=task_id)
    fallback_count = 0
    model_action_count = 0
    debug_events: list[str] = []

    while not observation.done and env.state.step_count < env.state.max_steps:
        action, source, raw_text = choose_action(
            client,
            model_name,
            observation,
            request_timeout_s=request_timeout_s,
        )
        if source != "model":
            fallback_count += 1
            debug_events.append(
                f"step={env.state.step_count + 1} source={source} "
                f"fallback_action={action.model_dump(mode='json', exclude_none=True)} "
                f"raw_output={preview_text(raw_text)}"
            )
        else:
            model_action_count += 1
        observation = env.step(action)

    if not env.state.done:
        observation = env.step(FinanceAction(action_type=ActionType.FINALIZE))

    grade = env.grade_episode()
    return {
        "task_id": task_id,
        "score": grade.score,
        "categorized_accuracy": grade.categorized_accuracy,
        "completion_ratio": grade.completion_ratio,
        "invalid_action_rate": grade.invalid_action_rate,
        "finalized": grade.finalized,
        "premature_finalize": grade.premature_finalize,
        "steps": env.state.step_count,
        "fallback_count": fallback_count,
        "model_action_count": model_action_count,
        "fallback_driven": fallback_count > model_action_count,
        "notes": grade.notes,
        "debug_events": debug_events,
    }


def print_summary(results: list[dict[str, Any]]) -> None:
    """Print a clear per-task and aggregate score summary."""

    print("Baseline Finance Evaluation")
    print("==========================")
    for result in results:
        print(
            f"{result['task_id']}: score={result['score']:.4f} "
            f"accuracy={result['categorized_accuracy']:.4f} "
            f"completion={result['completion_ratio']:.4f} "
            f"steps={result['steps']} model_actions={result['model_action_count']} "
            f"fallbacks={result['fallback_count']} "
            f"fallback_driven={str(result['fallback_driven']).lower()}"
        )
        if result["notes"]:
            print("  notes: " + "; ".join(result["notes"]))
        for event in result["debug_events"]:
            print("  debug: " + event)

    average_score = sum(result["score"] for result in results) / len(results)
    print("--------------------------")
    print(f"overall_average={average_score:.4f}")


def main() -> None:
    """Run the baseline across all implemented tasks."""

    config = load_config()
    client = OpenAI(base_url=config.api_base_url, api_key=config.hf_token)
    results = [
        run_task(client, config.model_name, task_id, config.request_timeout_s)
        for task_id in TASK_IDS
    ]
    print_summary(results)


if __name__ == "__main__":
    main()
