# Evaluation & Grading Strategy

This framework serves as a rigorous benchmark for LLM structured reasoning. Unlike generative NLP tasks (where evaluation is subjective or relies on an LLM-as-a-judge), this environment employs a **100% deterministic grading algorithm**.

## The Zero-Leak Guarantee

To ensure reliable benchmarking:
- **No Ground Truth in Prompts**: The environment's `reset()` and `step()` functions instantiate the scenario dynamically without embedding the target category mapping in the task description.
- **Grader Isolation**: The internal `state()` function exposes the answer keys to the orchestrator *only* after processing is complete. The LLM cannot access this payload.

## Difficulty Levels

The environment provides 3 built-in tasks (`task_id`) representing expanding operational difficulties:

1. **`easy_budget_cleanup_v1` (Easy)**
   - Tests basic natural language association.
   - Minimal ambiguity, clean strings (e.g., mapping `Walmart Supercenter` to `groceries`).
   - Requires zero multi-hop reasoning.

2. **`medium_ambiguous_ledger_v1` (Medium)**
   - Introduces ambiguous string matching and edge case mapping.
   - Tests the LLM's ability to differentiate contextual definitions (e.g., a subscription service vs. a one-time charge, or an internal account transfer vs. an external payment).

3. **`hard_operational_ledger_v1` (Hard)**
   - Simulates realistic, extremely messy real-world ledgers.
   - Includes highly similar merchant string matches, complex partial refunds, and fee classification.
   - Serves as the ultimate pressure-test for model consistency over high step counts.

## Reward Shaping

The environment utilizes sparse and dense reward signals to train or evaluate agents:
- **Positive Dense Rewards**: Incremental `+x` rewards for each correct categorization, proving partial progress.
- **Negative Penalties**: `-x` applied for invalid actions (e.g., proposing an unsupported category or finalizing prematurely), effectively penalizing hallucinated actions and breaking infinite loop loops.
- **Terminal Reward Matrix**: The final episode score is bound strictly within the `[0.0, 1.0]` internal metric constraint required by OpenEnv validators. 

At the end of an episode, `inference.py` calculates the exact overall accuracy and completion ratio deterministically.
