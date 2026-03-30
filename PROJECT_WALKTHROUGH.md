# PROJECT_WALKTHROUGH.md

## Purpose
This document explains the current OpenEnv finance categorizer project in plain language. It is meant for someone who wants to understand:
- what the project is
- what data models exist
- how the environment behaves
- how grading works
- what is implemented today
- what is still planned

Read this after `PROJECT.md` if you want the practical system walkthrough instead of the planning view.

---

## 1. Big Picture
This project is an OpenEnv environment where an AI agent is given messy financial transactions and must clean them up by assigning the correct category to each one.

The agent works step by step:
1. it sees a batch of transactions
2. it chooses an action
3. the environment updates its state
4. the environment returns a reward and a new observation
5. at any point, the episode can be graded deterministically against hidden ground truth

Today, the environment supports:
- an easy task
- a medium task
- deterministic grading for both

The hard task is still planned.

---

## 2. Repo Areas
Important files:
- `finance_env/models.py`: typed models for actions, observations, state, rewards, fixtures, and grading results
- `finance_env/server/finance_env_environment.py`: the environment logic
- `finance_env/grading.py`: deterministic grader functions
- `tests/test_finance_environment.py`: behavior and grading tests
- `PLAN.md`: milestone status
- `TASKS.md`: checklist of concrete work
- `PROGRESS.md`: current status and validation history
- `DECISIONS.md`: architecture and tradeoff decisions

---

## 3. Core Concepts

### 3.1 Transactions
A transaction is the raw item the agent must process.

Each transaction includes:
- `transaction_id`
- `merchant`
- `amount`
- `currency`
- `posted_date`
- `memo`
- `channel`

Example:
- merchant: `APPLE.COM/BILL`
- amount: `-10.99`
- memo: `iCloud+ 2TB monthly plan`

The agent must look at these fields and decide the correct category.

### 3.2 Categories
The category taxonomy is fixed for v1:
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

These categories are the label space for the environment.

### 3.3 Actions
The current public action space is intentionally small:
- `categorize_transaction`
- `finalize`

Example:
```python
FinanceAction(
    action_type="categorize_transaction",
    transaction_id="txn_001",
    category="groceries",
)
```

Or:
```python
FinanceAction(action_type="finalize")
```

This is the current minimal interaction loop. Split actions, duplicate handling, and anomaly actions are still planned for later milestones.

### 3.4 Observation
The observation is what the agent sees after `reset()` and each `step()`.

It includes:
- task id
- task description
- difficulty
- allowed actions
- allowed categories
- unresolved transactions
- processed ledger entries
- ledger summary
- action history
- warnings
- current transaction hint
- remaining step budget
- last reward

Important:
- the observation does not expose the hidden answer key
- the observation does not expose correctness flags for already processed transactions

### 3.5 Public State
The environment also exposes a typed `FinanceState`.

This public state includes:
- episode metadata
- task metadata
- transaction queue
- processed entries
- action history
- warnings
- invalid action count
- cumulative reward
- last reward

Important correction:
- public `state` is not the hidden ground truth anymore
- hidden answer data is stored privately inside the environment instance and is not returned through the normal state API

### 3.6 Hidden Ground Truth
The environment keeps a private answer key per episode.

Example shape:
```python
{
    "txn_001": "groceries",
    "txn_002": "utilities",
}
```

This private data is used for:
- reward calculation
- deterministic grading

It is not exposed through public observation or public state.

### 3.7 Reward
Reward is step-level feedback.

Current reward behavior includes:
- positive reward for correct categorization
- negative reward for incorrect categorization
- negative reward for invalid actions
- negative reward for premature finalize
- end-of-episode completion bonus
- small per-step penalty

This makes the reward non-sparse and useful during the episode, not only at the end.

---

## 4. Environment Lifecycle

### 4.1 `reset()`
`reset()` starts a new episode.

It:
- chooses a deterministic fixture by `task_id`
- loads that task's transactions
- resets counters
- clears processed entries
- prepares private hidden answer data
- returns the initial observation

Examples:
```python
env.reset()
```
Defaults to the easy task.

```python
env.reset(task_id="medium_ambiguous_ledger_v1")
```
Loads the medium task.

### 4.2 `step(action)`
`step()` takes one action and updates the episode.

For `categorize_transaction`, the environment:
1. validates the action
2. checks the hidden answer internally
3. records the chosen category in the ledger
4. updates reward
5. appends action history
6. returns a new observation

For `finalize`, the environment:
1. marks the episode done
2. computes completion bonus
3. applies premature-finalize penalty if needed
4. returns the final observation

### 4.3 `state`
`state` returns the current public typed environment state.

It is useful for:
- debugging
- testing
- inspecting the current ledger

It is not meant to reveal hidden ground truth.

### 4.4 `grade_episode()`
`grade_episode()` computes a deterministic score for the current episode.

The grader:
- compares processed entries with the private answer key
- computes categorized accuracy
- computes completion ratio
- penalizes premature finalize
- penalizes invalid action rate
- clamps score into `[0.0, 1.0]`

This is separate from reward.

---

## 5. Reward vs Grader

### Reward
Reward is local and step-by-step.

Use it to answer:
- Was that last action useful?
- Was it harmful?
- Should the agent keep doing things like that?

### Grader
The grader is episode-level evaluation.

Use it to answer:
- How good was the overall result?
- Did the final ledger end up correct?
- Did the agent finalize too early?

Important:
- reward guides behavior during the run
- grader judges performance across the whole episode

---

## 6. Current Tasks

### Easy task
Task id:
- `easy_budget_cleanup_v1`

Purpose:
- obvious everyday merchants
- low ambiguity
- single category per transaction

Examples:
- supermarket -> groceries
- utility bill -> utilities
- payroll -> income

### Medium task
Task id:
- `medium_ambiguous_ledger_v1`

Purpose:
- ambiguous merchants
- transfer-versus-income confusion
- subscription-versus-shopping confusion
- slightly more realistic interpretation of memo and merchant data

Examples:
- `APPLE.COM/BILL` with cloud-plan memo -> subscriptions
- `Zelle` incoming transfer -> transfer, not income
- `CVS Pharmacy` prescription -> healthcare
- `AMZN Mktp US` household goods -> shopping

### Hard task
Still planned.

The hard task is expected to introduce richer cases such as:
- split transactions
- duplicates
- anomalies
- tighter step budget

---

## 7. Current Grading Logic
The current grader is deterministic and fixture-based.

It scores:
- category accuracy on processed transactions
- completion ratio across all transactions
- whether the episode was finalized cleanly
- invalid action rate

The score is clamped into `[0.0, 1.0]`.

This means:
- perfect complete run can score `1.0`
- wrong labels reduce score
- premature finalize reduces score
- invalid actions reduce score

Because fixtures and answers are fixed, the same state always gives the same grade.

---

## 8. What Is Implemented vs Planned

### Implemented
- typed finance models
- easy task
- medium task
- deterministic easy grader
- deterministic medium grader support
- reward shaping for current categorization flow
- hidden-answer protection in public observation/state
- tests for easy and medium task behavior

### Planned
- hard task
- hard grader
- split actions
- duplicate/anomaly handling
- stronger anti-loop penalties
- baseline script
- Docker and Hugging Face validation
- final README rewrite
- `openenv validate`

---

## 9. Future Scope And Roadmap

This section explains what the project is expected to grow into, and what is intentionally not finished yet.

### 9.1 Near-Term Next Steps
These are the next logical project steps based on the current milestone plan:
- add the hard task fixture
- add the hard-task deterministic grader
- expand reward shaping only where the hard task truly needs it
- decide whether split transactions are necessary for the first submission-ready hard task

The main idea is to keep building outward from the stable easy/medium foundation instead of rewriting the current loop.

### 9.2 Planned Environment Expansion
The likely next feature areas are:
- split transactions for mixed-purpose purchases
- duplicate or anomaly handling actions
- tighter step budgets for harder tasks
- task-specific grading components for richer workflows

These are planned because they make the environment more realistic, but they are being deferred until the hard task is implemented cleanly.

### 9.3 Planned Submission Work
After the three tasks and graders are complete, the project still needs:
- baseline inference script using the OpenAI API client
- OpenEnv validation
- Docker verification
- Hugging Face Space readiness
- final README rewrite
- full submission checklist pass

These are required for the hackathon, but they are intentionally sequenced after the core environment and grading logic.

### 9.4 Scope Boundaries
The project is intentionally not trying to become a full financial product.

Out of scope for this version:
- live bank integrations
- OCR or receipt parsing
- authentication systems
- subjective budgeting systems with user-specific custom taxonomies
- large multi-user backend behavior

The goal is a benchmark-quality, deterministic finance workflow simulator, not a production banking app.

### 9.5 Design Principle For Future Work
Future changes should preserve these rules:
- keep the taxonomy stable unless there is a strong reason to change it
- keep fixtures explicit and deterministic
- do not leak hidden answers through observation or public state
- prefer small extensions of the current loop over large rewrites
- add complexity only when it improves realism without damaging reproducibility

---

## 10. How To Test It

Run the tests:
```powershell
.\.venv\Scripts\pytest -q
```

Try the easy task interactively:
```powershell
@'
from finance_env.server.finance_env_environment import FinanceEnvironment
from finance_env.models import FinanceAction, ActionType, CategoryName

env = FinanceEnvironment()
obs = env.reset()
print(obs.model_dump())

obs = env.step(FinanceAction(
    action_type=ActionType.CATEGORIZE_TRANSACTION,
    transaction_id="txn_001",
    category=CategoryName.GROCERIES,
))
print(obs.model_dump())

print(env.grade_episode().model_dump())
'@ | .\.venv\Scripts\python -
```

Try the medium task interactively:
```powershell
@'
from finance_env.server.finance_env_environment import FinanceEnvironment
from finance_env.models import FinanceAction, ActionType, CategoryName

env = FinanceEnvironment()
obs = env.reset(task_id="medium_ambiguous_ledger_v1")
print(obs.task_id)
print(obs.unresolved_transactions[0].model_dump())

obs = env.step(FinanceAction(
    action_type=ActionType.CATEGORIZE_TRANSACTION,
    transaction_id="txn_m001",
    category=CategoryName.SUBSCRIPTIONS,
))
print(obs.model_dump())

print(env.grade_episode().model_dump())
'@ | .\.venv\Scripts\python -
```

---

## 11. Simple Mental Model
- Models = what exists
- Environment = what happens after an action
- Reward = how the agent is guided step by step
- Grader = how the final result is judged

If you want the shortest correct summary of the project, use this:

> This is a deterministic OpenEnv benchmark where an agent cleans up messy personal finance transactions by categorizing them over multiple steps, receives reward feedback during the episode, and is graded against private ground truth at the end.
