# DECISIONS.md

## 2026-03-28 - Choose the environment domain
**Decision**
Use a personal finance transaction categorization environment.

**Why**
- Real-world repeated task.
- Clear structured action space.
- Deterministic grading is feasible.
- Strong easy -> medium -> hard progression.
- Good fit for the competition emphasis on utility and grader quality.

**Alternatives considered**
- email triage
- bug triage
- customer support routing

**Consequence**
The project will focus on transaction processing, category assignment, split handling, and anomaly/duplicate review.

---

## 2026-03-28 - Prefer fixture-based deterministic tasks for v1
**Decision**
Use handcrafted task fixtures instead of procedural generation in the first version.

**Why**
- Faster to implement under time pressure.
- Easier to grade deterministically.
- Easier to debug and document.

**Consequence**
The first version may be less varied, but it will be more reliable and competition-safe.

---

## 2026-03-28 - Prioritize correctness over maximal realism
**Decision**
Keep category schema and transaction mechanics limited enough to finish all mandatory deliverables.

**Why**
A fully realistic finance system would add too much complexity and create grading ambiguity.

**Consequence**
The environment will model a believable but bounded finance workflow, which is appropriate for a benchmark environment.

---

## 2026-03-29 - Lock the v1 category taxonomy
**Decision**
Freeze the first-pass taxonomy to 14 categories:
`groceries`, `dining`, `transport`, `utilities`, `rent`, `subscriptions`, `healthcare`, `shopping`, `travel`, `entertainment`, `transfer`, `income`, `fees`, `uncategorized`.

**Why**
- Matches the strongest overlap between the root project docs and the Milestone 1 implementation plan.
- Keeps the environment realistic without making grading or fixture authoring too broad.
- Leaves room for medium and hard tasks without changing the public schema later.

**Consequence**
Easy, medium, and hard tasks should all reuse this taxonomy unless a later documented schema revision becomes necessary.

---

## 2026-03-29 - Finalize ends the episode even when incomplete
**Decision**
Treat `finalize` as a terminal action. If unresolved transactions remain, the environment ends the episode and applies a deterministic penalty plus a reduced completion bonus.

**Why**
- Keeps episode boundaries explicit and simple.
- Avoids ambiguous retry behavior after a user claims the ledger is complete.
- Supports easy deterministic grading based on the final ledger snapshot.

**Consequence**
Agents must avoid premature finalize calls. The observation and tests should make this behavior clear.

---

## 2026-03-29 - Separate public state from hidden grading data
**Decision**
Keep the answer key private to the environment instance and grader path rather than including it in the public `FinanceState` or `FinanceObservation`.

**Why**
- Prevents label leakage through the normal environment API.
- Preserves the integrity of benchmark evaluation and grader quality.
- Still allows deterministic reward shaping and grading using internal-only data.

**Consequence**
The environment now uses a sanitized public `FinanceState`, while hidden ground truth is stored separately and only consumed by grader logic and internal transitions.

---

## 2026-03-29 - Add task selection through deterministic fixture ids
**Decision**
Select tasks by `task_id` during `reset(...)` while keeping the action schema unchanged.

**Why**
- Adds medium-task support with minimal disruption to the working easy-task loop.
- Keeps fixture-based tasks explicit and reproducible.
- Avoids premature expansion of the action model before medium and hard requirements are clearer.

**Consequence**
Easy and medium tasks now share the same environment loop and public schema, while task-specific behavior is driven by deterministic fixture data and grader dispatch.
