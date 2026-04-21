# PROJECT.md

## Project Title
OpenEnv Personal Finance Transaction Categorizer

## One-Sentence Summary
Build a real-world OpenEnv environment where an agent processes consumer finance transactions into a clean, categorized ledger with deterministic grading and reward shaping.

## Problem Statement
People repeatedly spend time cleaning up their bank and credit-card transaction histories for budgeting, expense review, and bookkeeping. Merchant names are messy, categories are inconsistent, some transactions should be split across multiple categories, and others should be flagged for review. This project turns that repeated finance workflow into an OpenEnv environment suitable for training and evaluating agents.

This directly satisfies the requirement that the environment simulate a real-world task rather than a game or toy. The uploaded brief also requires full OpenEnv compatibility, three graded tasks, reward shaping, baseline evaluation, containerization, and documentation. See the uploaded brief for the competition constraints and evaluation criteria. 

## Why This Domain Is Strong
- Real-world utility: budgeting and bookkeeping are recurring user problems.
- Clear, structured action space: categorize, split, flag, finalize.
- Deterministic grading: compare final ledger against ground truth.
- Strong difficulty ladder: obvious merchants → ambiguous merchants → splits/anomalies.
- Good reward shaping opportunities across a full trajectory.

## Product Goal
The environment should allow an agent to interact step-by-step with a queue of financial transactions and produce a correctly processed ledger.

A successful agent should be able to:
- assign accurate categories
- distinguish transfers from expenses
- detect duplicates or anomalies
- split mixed-purpose transactions where appropriate
- complete the ledger efficiently with minimal harmful actions

## Users / Evaluators
Primary evaluators:
- OpenEnv competition validators
- automated benchmark agents
- human reviewers judging utility, design, creativity, and quality

Potential real-world user analogs:
- personal budgeting users
- bookkeeping assistants
- finance operations tools
- agent-training researchers

## Scope
### In scope
- Single-episode transaction processing environment
- Structured observation and action models
- Three tasks with increasing difficulty
- Deterministic graders with scores in `[0.0, 1.0]`
- Reward shaping over the trajectory
- Baseline evaluation script
- Dockerized deployment
- Hugging Face Space deployment path
- README and environment documentation

### Out of scope
- Live bank integrations
- OCR for receipts
- authentication / user account system
- production financial compliance workflows
- highly subjective categorization schemes
- large-scale multi-user backend

## Core Environment Concept
Each episode presents a budget profile and a transaction set.

The agent iteratively processes transactions. For each transaction, the agent may:
- assign a category
- split the amount across multiple categories
- mark it as transfer / income / fee where applicable
- flag it for manual review
- mark suspected duplicate
- finalize the episode

The environment then updates the ledger and provides reward feedback.

## Proposed State Model
The internal state should include at least:
- task id
- difficulty level
- transaction list with stable ids
- current unresolved transactions
- actions taken so far
- category map
- answer key for grader use
- duplicate / anomaly metadata
- current score components
- step counter and max steps
- done flag

## Proposed Observation Model
The observation exposed to the agent should include at least:
- task description
- allowed actions
- allowed categories
- visible transaction fields (id, merchant, amount, currency, date, memo, channel)
- current ledger summary
- unresolved transaction count
- action history summary
- warnings or validation messages
- remaining step budget if applicable

Do not expose the hidden answer key in observation.

## Proposed Action Model
Recommended initial action schema:
- `action_type`: one of `categorize`, `split`, `flag_review`, `mark_duplicate`, `finalize`
- `transaction_id`: required except for `finalize`
- `category`: for `categorize`
- `splits`: list of `{category, amount}` for `split`
- `reason`: optional explanation / note
- `target_transaction_id`: optional for duplicate marking

The exact schema can be refined during implementation, but it should stay compact and deterministic.

## Reward Design Goals
Reward should provide meaningful signal during the episode, not only at the end.

Recommended shaping:
- positive reward for correct categorization
- smaller positive reward for correct partial split
- positive reward for correctly flagging anomalies/duplicates
- penalty for invalid actions
- penalty for incorrect categories
- penalty for unnecessary review flags
- penalty for excessive steps or loops
- end-of-episode bonus based on final ledger quality

Reward must not be trivially exploitable.

## Task Set
### Task 1 — Easy: Everyday Budget Cleanup
Characteristics:
- common merchants
- obvious categories
- no splits
- minimal ambiguity

Examples:
- supermarket → groceries
- electric bill → utilities
- streaming service → subscriptions

Goal:
Produce a correctly categorized ledger with near-perfect accuracy.

### Task 2 — Medium: Ambiguous and Operationally Tricky Ledger
Characteristics:
- ambiguous merchants
- subscriptions vs shopping confusion
- transfer vs expense confusion
- possible duplicates

Goal:
Correctly process realistic noisy finance records with stronger reasoning.

### Task 3 — Hard: Mixed-Purpose and Exception Handling
Characteristics:
- transactions requiring splits
- partial refunds
- suspicious outliers
- duplicate candidate pairs
- tighter action budget

Goal:
Resolve a complex ledger while preserving correctness and efficiency.

## Grading Design
Each task should have a deterministic grader that compares the final episode state to a hidden answer key.

Possible score components:
- category accuracy
- split accuracy
- duplicate/anomaly handling accuracy
- invalid-action rate
- efficiency / step usage
- completion percentage

Suggested overall score:
weighted normalized score clamped to `[0.0, 1.0]`.

## Non-Functional Requirements
From the uploaded brief, the project must also include:
- complete OpenEnv interface
- typed models
- `openenv.yaml`
- baseline inference script named `inference.py` at the root, using OpenAI client with `API_BASE_URL`, `MODEL_NAME`, and `HF_TOKEN` from env vars
- strict `[START] / [STEP] / [END]` structured stdout logging contract
- Hugging Face Space deployability
- working Dockerfile
- clear README documentation

## Constraints
- Keep design finishable within the available time.
- Prioritize determinism and validation over excessive realism.
- Prefer explicit fixture-based tasks over procedural generation for v1.
- Keep categories limited and documented.
- Ensure all competition-critical deliverables exist before polishing extras.

## Deliverables
- source code for the environment
- typed models
- task fixtures
- graders
- reward logic
- baseline evaluation script
- Dockerfile
- `openenv.yaml`
- README
- HF Space deployment-ready repo

## Success Criteria
This project is successful if:
- the environment models a believable finance workflow
- tasks are clearly differentiated and deterministic
- graders are reliable and non-constant
- baseline runs reproducibly
- OpenEnv validation passes
- Docker and local execution work
- the repo is clear enough for reviewers to understand quickly
