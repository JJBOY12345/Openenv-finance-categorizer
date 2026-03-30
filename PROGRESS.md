# PROGRESS.md

## Current Status
- Domain selected: **Personal Finance Transaction Categorizer**
- Current phase: Milestone 1 complete, Milestone 2 core complete, Milestone 3 partially complete
- Overall state: easy and medium categorization tasks are implemented with deterministic graders and hidden labels kept private
- Last updated: 2026-03-29

## What Has Been Decided
- The environment simulates a real bookkeeping and budgeting workflow.
- The v1 taxonomy is locked to 14 categories: groceries, dining, transport, utilities, rent, subscriptions, healthcare, shopping, travel, entertainment, transfer, income, fees, uncategorized.
- The current pass supports deterministic easy and medium task fixtures, with hard still pending.
- Task selection now happens through deterministic `task_id` values at reset time.
- `finalize` is a terminal action even if transactions remain unresolved; premature finalization is penalized.
- Hidden answer keys must remain private and not be exposed through normal public state or observation payloads.
- Deterministic grading and reproducibility remain higher priority than maximal realism.

## Completed
- Replaced the generated echo scaffold models with typed finance models in `finance_env/models.py`.
- Added typed support models for transactions, ledger entries, reward breakdowns, action history, task fixtures, and internal state.
- Implemented a deterministic easy-task fixture in `finance_env/server/finance_env_environment.py`.
- Implemented coherent `reset()`, `step()`, and `state` behavior for the easy task.
- Added explicit action validation for `categorize_transaction` and `finalize`.
- Added first-pass reward shaping for:
  - correct categorization
  - incorrect categorization
  - invalid actions
  - premature finalize
  - final completion bonus
- Updated the client and package exports to match the finance schema.
- Added focused environment tests under `tests/`.
- Added `pytest.ini` to keep default test discovery scoped to the environment tests.
- Removed hidden-answer leakage from public state and observation models.
- Extracted deterministic easy-task grading into `finance_env/grading.py`.
- Added easy-task grader tests covering full-credit, wrong-label, premature-finalize, and hidden-answer behavior.
- Added a deterministic medium task fixture with ambiguous merchants and transfer-versus-expense confusion.
- Extended grading support to dispatch between easy and medium categorization tasks.
- Added medium-task tests for reset/task selection, full-credit grading, and degraded grading under wrong categorization plus premature finalize.
- Added `PROJECT_WALKTHROUGH.md` as a plain-language system explainer for readers and contributors.
- Expanded `PROJECT_WALKTHROUGH.md` with future scope and roadmap notes.
- Updated `TASKS.md` and `DECISIONS.md` to reflect the completed milestone work and locked decisions.

## In Progress
- Extending the environment from easy/medium to the full easy/medium/hard ladder.
- Designing the hard task on top of the now-separated public/private state model.

## Not Started
- Hard task fixture
- Deterministic hard grader
- Full reward shaping for split, duplicate, and anomaly handling
- Baseline script
- Docker and Hugging Face deployment validation
- README completion
- OpenEnv validation

## Known Risks
- Split-transaction design may still become too complex if introduced too early.
- The current reward shaping does not yet penalize looping beyond the per-step cost.
- Pytest still emits a Windows cache warning in this workspace even though the test run passes.

## Recommended Next Step
Add the hard task fixture and hard-task grader using the same hidden-answer pattern, then expand the action schema only if the hard task truly requires split or anomaly-specific actions.

## Validation Log
- `python` smoke test against `FinanceEnvironment.reset()` / `step()` / `state`: passed
- `pytest -q tests --basetemp .pytest_tmp`: 4 passed
- `python` smoke test confirming public state does not expose `answer_key` and grader remains callable: passed
- `python` smoke test confirming `reset(task_id="medium_ambiguous_ledger_v1")` selects the medium fixture and grades deterministically: passed
- `pytest -q`: 11 passed
- Note: the default pytest run now works after adding `pytest.ini`, but it still emits a non-blocking Windows cache warning in this workspace

## Notes for Next Session
Keep fixtures explicit and version-controlled. Reuse the sanitized public state plus private answer-key pattern for the hard task so grader logic stays deterministic without leaking labels.
