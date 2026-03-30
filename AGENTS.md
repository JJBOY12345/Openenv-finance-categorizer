# AGENTS.md

## Mission
Build a production-quality OpenEnv environment for **personal finance transaction categorization and bookkeeping assistance**.

The environment must simulate a real task people repeatedly face: reviewing messy bank and card transactions, assigning the correct budget category, handling ambiguous merchants, splitting mixed-purpose transactions, flagging anomalies, and maintaining a clean ledger.

The final environment must satisfy the competition brief, pass OpenEnv validation, support reproducible baseline evaluation, and be practical for training or benchmarking agents.

---

## Product Summary
This project is a real-world finance operations simulator. An agent interacts with a ledger-like environment through the standard OpenEnv `reset()` / `step()` / `state()` API and attempts to process transactions correctly.

Primary user stories to support:
- Categorize common transactions into budget categories.
- Handle ambiguous merchant names using transaction metadata.
- Split transactions when one line item belongs to multiple categories.
- Flag suspicious, duplicate, or outlier transactions for review.
- Finish each episode with a clean, auditable ledger state.

Suggested category families:
- groceries
- dining
- transport
- utilities
- rent
- subscriptions
- healthcare
- shopping
- travel
- entertainment
- transfer
- income
- fees
- uncategorized

---

## Absolute Requirements
The agent MUST ensure the environment includes all of the following:

1. **Real-world task simulation**
   - Must not be a toy or game.
   - Must model a genuine repeated finance workflow.

2. **OpenEnv spec compliance**
   - Typed Pydantic models for Observation, Action, Reward.
   - Implement `reset()`.
   - Implement `step(action)`.
   - Implement `state()`.
   - Include `openenv.yaml`.
   - Must pass `openenv validate` before submission.

3. **At least 3 tasks with deterministic graders**
   - easy
   - medium
   - hard
   - Each task must score in `[0.0, 1.0]`.
   - Graders must not be constant or random.

4. **Meaningful reward shaping**
   - Reward must provide partial progress signal.
   - Reward must penalize clearly bad behavior.
   - Reward cannot be purely sparse binary success/failure.

5. **Baseline inference script**
   - Uses OpenAI API client.
   - Reads credentials from environment variables.
   - Produces reproducible scores across the three tasks.

6. **Deployment readiness**
   - Working Dockerfile.
   - Deployable to Hugging Face Spaces.
   - Include required endpoints from the brief when applicable.

7. **Documentation**
   - README describing motivation, environment, action space, observation space, task difficulty, setup, usage, and baseline results.

---

## Disqualification / Failure Conditions
The agent MUST avoid all of the following:

- Building a toy problem unrelated to real finance workflows.
- Returning nearly constant grader scores regardless of behavior.
- Omitting the baseline script.
- Leaving Docker broken or untested.
- Leaving OpenEnv spec incomplete.
- Producing tasks with vague or subjective grading.
- Designing rewards that encourage infinite loops or no-op behavior.
- Adding complexity that makes completion unlikely within the time available.

---

## Recommended Environment Concept
Use a ledger-style environment with one transaction queue per episode.

A good episode contains:
- a user profile or budget profile
- one or more transactions awaiting processing
- current transaction pointer
- allowed categories
- prior actions taken
- ledger summary
- remaining unresolved ambiguity flags
- step count / turn budget

The environment should support actions such as:
- categorize transaction
- split transaction
- flag transaction for manual review
- mark duplicate
- request clarification metadata (if implemented)
- finalize ledger / finish episode

The observation should expose enough structured information for deterministic grading without leaking the exact answer key.

---

## Workflow Rules
For any substantial task, follow this order.

### Before coding
1. Read `PROJECT.md` fully.
2. Read `PLAN.md`, `TASKS.md`, and `TESTING.md`.
3. Confirm the current milestone in `PROGRESS.md`.
4. Work on the **smallest safe next step**.
5. Prefer finishing one milestone end-to-end rather than partially touching many areas.

### During coding
- Keep changes scoped to the current milestone.
- Prefer simple state machines and deterministic business logic.
- Reuse patterns from the OpenEnv course repo where helpful.
- Do not introduce speculative abstractions unless they clearly reduce risk.
- Keep category schema and reward logic explicit and inspectable.
- Preserve reproducibility.

### After each meaningful change
- Run the relevant tests/checks.
- Update `PROGRESS.md` with:
  - what changed
  - validation run
  - blockers
  - next step
- If a design decision changed, append it to `DECISIONS.md`.

---

## Engineering Rules
- Prefer deterministic logic over fuzzy heuristics where grading depends on correctness.
- Keep category mappings centralized.
- Make task fixtures explicit and version-controlled.
- Ensure every task has a ground-truth answer key usable by graders.
- Avoid hidden side effects in `step()`.
- Keep `state()` richer than `observation` if needed for debugging and grading.
- Use clear episode boundaries.
- Penalize destructive or nonsensical actions.
- Ensure invalid actions return informative `info` and sensible reward penalties.

---

## Task Design Rules
Every task should include:
- a natural-language task objective
- initial ledger / transaction data
- action budget if needed
- deterministic answer key
- grader implementation
- reward shaping logic
- expected difficulty rationale

### Suggested difficulty ladder
- **Easy**: obvious merchant-to-category mapping, no splits, little ambiguity.
- **Medium**: ambiguous merchants, recurring subscriptions, duplicate detection, transfer vs expense confusion.
- **Hard**: mixed-purpose transactions, partial refunds, split categories, anomalies, tighter step budget.

---

## File Responsibilities
- `AGENTS.md`: operating instructions for the coding agent.
- `PROJECT.md`: product requirements and concrete finance-domain definition.
- `PLAN.md`: milestone plan and implementation strategy.
- `TASKS.md`: actionable checklist.
- `PROGRESS.md`: current status log.
- `TESTING.md`: validation checklist and commands.
- `DECISIONS.md`: architecture and tradeoff log.

If a task changes behavior, update at least `PROGRESS.md` and any impacted design doc.

---

## Validation Rules
A task is not complete until the agent verifies the relevant parts below.

### Core behavior
- `reset()` returns a valid initial observation.
- `step()` mutates state correctly and returns valid observation/reward/done/info.
- `state()` returns current internal state cleanly.

### Grading
- Every task grader returns a score in `[0.0, 1.0]`.
- Graders are deterministic and tied to actual episode outcomes.
- Easy / medium / hard meaningfully differ.

### Reward shaping
- Correct partial progress yields incremental reward.
- Invalid or harmful actions incur penalties.
- No-op loops are discouraged.

### Packaging
- `openenv validate` passes.
- Docker builds.
- Local server runs.
- Baseline script runs end-to-end.

---

## Definition of Done
The project is done only when all of the following are true:
- OpenEnv environment works locally.
- Typed models and `openenv.yaml` are complete.
- Three finance tasks and graders work deterministically.
- Reward function gives meaningful dense-ish signal.
- Baseline script produces reproducible scores.
- Docker works.
- HF Space deployment path is documented.
- README explains the environment clearly.

---

## When to Stop and Reassess
Stop implementation and update the plan if any of these happen:
- task grading becomes subjective or non-deterministic
- reward shaping is fighting task correctness
- environment API is drifting from OpenEnv expectations
- current design cannot reasonably be finished on time
- state or action schema is becoming overly complicated

When this happens, simplify instead of expanding scope.
