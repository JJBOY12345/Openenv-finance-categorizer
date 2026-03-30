# PLAN.md

## Status Legend
- [x] Implemented
- [~] Partial / in progress
- [ ] Planned
- [!] Blocked

## Delivery Strategy
Prioritize competition-critical completeness over ambitious realism.

Current sequence status:
1. [x] Lock domain and action/state schemas
2. [x] Implement minimal valid environment core
3. [x] Implement easy task and grader first
4. [~] Add medium and hard tasks
5. [~] Add reward shaping and validation polish
6. [ ] Add baseline script
7. [ ] Add Docker / HF deployment docs
8. [ ] Finalize README and submission checks

---

## Milestone 1 - Project Scaffold and Schema Lock
**Status:** [x] Implemented

### Goal
Create a clean OpenEnv project skeleton and freeze the finance domain contract.

### Status by output
- [x] Project scaffold exists in repo
- [x] Typed models for Observation / Action / Reward exist
- [x] Initial category list is locked to 14 categories
- [x] Task fixture format exists
- [x] `openenv.yaml` draft exists
- [~] README skeleton exists only as generated scaffold and still needs project-specific rewrite

### Validation completed
- [x] Imports work
- [x] Models instantiate cleanly
- [x] Category schema is documented in code and decisions

### Exit criteria
- [x] Schema is stable enough to implement `reset()` / `step()` / `state()`

---

## Milestone 2 - Environment Core Loop
**Status:** [x] Implemented for current categorization flow

### Goal
Implement valid episode lifecycle and ledger state transitions.

### Status by output
- [x] `reset()` implementation
- [x] `step()` implementation
- [x] `state()` implementation
- [x] Transaction queue progression
- [x] Action validation
- [x] Done conditions
- [x] Public/private state separation to avoid label leakage
- [ ] Split-transaction handling
- [ ] Duplicate/anomaly action handling

### Validation completed
- [x] Manual smoke test of episode lifecycle
- [x] Invalid actions handled safely
- [x] State transitions deterministic
- [x] Public observation/state do not expose answer keys

### Exit criteria
- [x] Environment loop works on handcrafted task fixtures

---

## Milestone 3 - Task Fixtures and Graders
**Status:** [~] Partial

### Goal
Create three deterministic tasks with hidden answer keys and scoring.

### Status by output
- [x] Easy task fixture
- [x] Medium task fixture
- [ ] Hard task fixture
- [x] Easy grader
- [x] Medium grader support
- [ ] Hard grader
- [x] Score aggregation logic in `[0.0, 1.0]`
- [x] Hidden answer keys kept private while remaining available to graders

### Validation completed
- [x] Easy grader returns stable score for same final state
- [x] Medium grader returns stable score for same final state
- [x] Easy scores are not constant
- [x] Medium scores are not constant
- [ ] Hard task validation

### Exit criteria
- [ ] Easy / medium / hard can all be reset and graded independently

---

## Milestone 4 - Reward Shaping
**Status:** [~] Partial

### Goal
Make reward informative over the full trajectory.

### Status by output
- [x] Incremental reward logic for categorization
- [x] Penalties for invalid actions
- [x] Premature finalize penalty
- [x] End-of-episode completion bonus
- [ ] Anti-loop penalty strategy beyond per-step cost
- [ ] Split-specific reward logic
- [ ] Duplicate/anomaly reward logic

### Validation completed
- [x] Reward is not binary-only
- [x] Correct categorization increases reward
- [x] Wrong categorization lowers reward
- [x] Premature finalize is penalized
- [ ] Repeated no-op behavior is explicitly discouraged

### Exit criteria
- [ ] Reward visibly changes across easy / medium / hard behavior patterns

---

## Milestone 5 - Baseline Evaluation Script
**Status:** [ ] Planned

### Goal
Provide reproducible baseline inference over all tasks.

### Status by output
- [ ] Baseline script using OpenAI API client
- [ ] Env-var based credential loading
- [ ] Deterministic task ordering / settings
- [ ] Score reporting output

### Exit criteria
- [ ] Baseline completes successfully and writes a consistent summary

---

## Milestone 6 - Packaging and Deployment
**Status:** [ ] Planned

### Goal
Make the project submission-ready.

### Status by output
- [ ] Dockerfile verified
- [ ] Local run instructions
- [ ] HF Space deployment instructions
- [ ] Required endpoints documented / exposed
- [ ] README completion

### Exit criteria
- [ ] Repo is ready for local validation and HF deployment

---

## Milestone 7 - Final QA and Submission Readiness
**Status:** [ ] Planned

### Goal
Run a full pre-submission checklist.

### Status by output
- [ ] Final validation log
- [ ] Baseline scores recorded
- [ ] README polished
- [ ] Docs cross-checked

### Exit criteria
- [ ] All competition-critical items are green

---

## Scope Guardrails
If time gets tight, simplify in this order:
1. reduce category count
2. reduce task fixture size
3. simplify split mechanics
4. simplify anomaly logic

Do **not** cut:
- OpenEnv compliance
- 3 tasks with graders
- baseline script
- Dockerfile
- deterministic scoring
