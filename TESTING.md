# TESTING.md

## Testing Philosophy
Use deterministic, repeatable checks that map directly to competition requirements. Validate core environment behavior first, then graders, then packaging and deployment.

---

## Core Manual Smoke Tests
### Reset
- `reset()` returns a valid initial observation object.
- unresolved transaction count is correct.
- step counter resets.
- done flag is false.

### Step
- valid `categorize` action updates ledger correctly.
- valid `split` action updates ledger correctly.
- invalid action returns penalty and useful info.
- duplicate/anomaly marking updates state as expected.

### State
- `state()` reflects current internal state.
- hidden grader metadata is available internally if intended.
- observation does not leak hidden answer key.

---

## Automated Validation Targets
Run these once implemented.

- environment unit tests
- grader tests
- reward tests
- `openenv validate`
- baseline script smoke test
- `docker build`
- local container run test

---

## Grader Test Checklist
For each of easy / medium / hard:
- perfect action sequence yields score near or equal to `1.0`
- clearly wrong sequence yields materially lower score
- repeated runs on same final state yield same score
- grader output is clamped to `[0.0, 1.0]`

Additional checks:
- grader is sensitive to category mistakes
- grader is sensitive to split mistakes
- grader is sensitive to duplicate/anomaly mistakes where applicable
- grader is not constant

---

## Reward Test Checklist
- correct categorization increases reward
- wrong categorization decreases reward or avoids positive reward
- correct split gives positive signal
- invalid action incurs penalty
- repeated low-value looping behavior is penalized
- finalization before completion is penalized if appropriate
- reward does not incentivize gaming unrelated to grader success

---

## Baseline Validation
The baseline script must:
- load API credentials from environment variables
- run against all three tasks
- output per-task scores and aggregate score
- complete without manual intervention
- behave reproducibly under same configuration

Local baseline run:
```powershell
$env:API_BASE_URL="https://router.huggingface.co/v1"
$env:MODEL_NAME="Qwen/Qwen2.5-7B-Instruct:together"
$env:HF_TOKEN="<YOUR_HF_TOKEN>"
.\.venv\Scripts\python inference.py
```

Expected baseline behavior:
- iterates over `easy_budget_cleanup_v1`, `medium_ambiguous_ledger_v1`, and `hard_operational_ledger_v1`
- prints one summary line per task
- prints an overall average score
- falls back to a deterministic local categorization heuristic when model output is malformed
- prints debug lines when request failure or parsing failure triggers fallback
- reports per-task `model_actions`, `fallbacks`, and whether the run was fallback-driven

---

## Docker / Deployment Validation
- `docker build` succeeds
- container starts cleanly
- environment responds to expected API calls
- local run path matches README
- HF Space deployment instructions are complete

---

## README Validation
README must include:
- project motivation
- why finance categorization is a real-world task
- action space definition
- observation space definition
- task descriptions and difficulty
- setup instructions
- local run instructions
- Docker instructions
- baseline results
- validation notes if relevant

---

## Pre-Submission Checklist
All of these should be green before submission:
- OpenEnv validation passes
- Docker builds and runs
- 3+ tasks exist
- each task has a grader
- all graders output in `[0.0, 1.0]`
- baseline script runs successfully
- README is complete
- HF Space deployment path is tested or ready
- no obvious disqualification criteria remain
