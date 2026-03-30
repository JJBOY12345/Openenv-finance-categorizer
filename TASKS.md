# TASKS.md

## Priority Legend
- P0 = mandatory for submission
- P1 = strong quality improvement
- P2 = nice to have

---

## Milestone 1 - Scaffold and Schema Lock
- [x] (P0) Initialize OpenEnv project scaffold
- [x] (P0) Define finance category list
- [x] (P0) Define Observation model
- [x] (P0) Define Action model
- [x] (P0) Define Reward model
- [x] (P0) Draft `openenv.yaml`
- [x] (P0) Decide fixture format for tasks and answer keys
- [ ] (P1) Create README skeleton

## Milestone 2 - Core Environment Loop
- [x] (P0) Implement episode state container
- [x] (P0) Implement `reset()`
- [x] (P0) Implement `step()`
- [x] (P0) Implement `state()`
- [x] (P0) Add action validation logic
- [x] (P0) Add done conditions
- [x] (P1) Add transaction history summary to observation

## Milestone 3 - Task Fixtures and Graders
- [x] (P0) Create easy task fixture
- [x] (P0) Create medium task fixture
- [ ] (P0) Create hard task fixture
- [x] (P0) Implement deterministic grader for easy task
- [x] (P0) Implement deterministic grader for medium task
- [ ] (P0) Implement deterministic grader for hard task
- [x] (P0) Clamp and normalize scores to `[0.0, 1.0]`
- [ ] (P1) Add fixture comments explaining why each task is easy/medium/hard

## Milestone 4 - Reward Shaping
- [x] (P0) Reward correct categorization
- [x] (P0) Penalize incorrect categorization
- [ ] (P0) Reward correct split behavior
- [ ] (P0) Reward correct duplicate/anomaly handling
- [x] (P0) Penalize invalid actions
- [ ] (P0) Penalize wasteful repeated actions / loops
- [x] (P1) Add end-of-episode completion bonus

## Milestone 5 - Baseline Evaluation
- [ ] (P0) Create baseline inference script
- [ ] (P0) Load `OPENAI_API_KEY` from environment
- [ ] (P0) Run baseline on all three tasks
- [ ] (P0) Print structured per-task and aggregate scores
- [ ] (P1) Persist baseline output to file for reproducibility

## Milestone 6 - Packaging and Deployment
- [ ] (P0) Create Dockerfile
- [ ] (P0) Verify local container run
- [ ] (P0) Confirm OpenEnv validation passes
- [ ] (P0) Document HF Space deployment steps
- [ ] (P0) Ensure required endpoints are documented/available
- [ ] (P0) Finalize README

## Milestone 7 - Final QA
- [ ] (P0) Run full local validation checklist
- [ ] (P0) Record baseline results in README
- [ ] (P0) Check for disqualification risks
- [ ] (P0) Confirm repo is submission-ready

---

## Suggested First Execution Order
1. lock category list and action schema
2. implement easy task only
3. make grader pass for easy task
4. generalize to medium and hard
5. add reward shaping
6. package and validate
