# OpenEnv Hackathon — Final Submission Requirements

## Pre-Submission Checklist (MANDATORY)

All must pass or submission is disqualified:

1. HF Space deploys
   - Space URL must return HTTP 200
   - Must respond correctly to /reset

2. OpenEnv spec compliance
   - openenv.yaml present
   - typed models used
   - step(), reset(), state() implemented
   - openenv validate passes

3. Dockerfile builds
   - docker build must succeed from repo root OR server/

4. Baseline reproduces
   - inference.py runs successfully
   - produces valid outputs
   - no crashes

5. 3+ tasks with graders
   - tasks exist
   - each task returns reward in [0.0, 1.0]
   - deterministic grading


NEW
Pre Validation Script

  stop_at "Step 1"
fi

log "${BOLD}Step 2/3: Running docker build${NC} ..."

if ! command -v docker &>/dev/null; then
  fail "docker command not found"
  hint "Install Docker: https://docs.docker.com/get-docker/"
  stop_at "Step 2"
fi

if [ -f "$REPO_DIR/Dockerfile" ]; then
  DOCKER_CONTEXT="$REPO_DIR"
elif [ -f "$REPO_DIR/server/Dockerfile" ]; then
  DOCKER_CONTEXT="$REPO_DIR/server"
else
  fail "No Dockerfile found in repo root or server/ directory"
  stop_at "Step 2"
fi

log "  Found Dockerfile in $DOCKER_CONTEXT"

BUILD_OK=false
BUILD_OUTPUT=$(run_with_timeout "$DOCKER_BUILD_TIMEOUT" docker build "$DOCKER_CONTEXT" 2>&1) && BUILD_OK=true

if [ "$BUILD_OK" = true ]; then
  pass "Docker build succeeded"
else
  fail "Docker build failed (timeout=${DOCKER_BUILD_TIMEOUT}s)"
  printf "%s\n" "$BUILD_OUTPUT" | tail -20
  stop_at "Step 2"
fi

log "${BOLD}Step 3/3: Running openenv validate${NC} ..."

if ! command -v openenv &>/dev/null; then
  fail "openenv command not found"
  hint "Install it: pip install openenv-core"
  stop_at "Step 3"
fi

VALIDATE_OK=false
VALIDATE_OUTPUT=$(cd "$REPO_DIR" && openenv validate 2>&1) && VALIDATE_OK=true

if [ "$VALIDATE_OK" = true ]; then
  pass "openenv validate passed"
  [ -n "$VALIDATE_OUTPUT" ] && log "  $VALIDATE_OUTPUT"
else
  fail "openenv validate failed"
  printf "%s\n" "$VALIDATE_OUTPUT"
  stop_at "Step 3"
fi

printf "\n"
printf "${BOLD}========================================${NC}\n"
printf "${GREEN}${BOLD}  All 3/3 checks passed!${NC}\n"
printf "${GREEN}${BOLD}  Your submission is ready to submit.${NC}\n"
printf "${BOLD}========================================${NC}\n"
printf "\n"

exit 0


NEW
Sample Inference Script 

"""
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return "hello"


async def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    env = await MyEnvV4Env.from_docker_image(IMAGE_NAME)

    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = await env.reset() # OpenENV.reset()
        last_echoed = result.observation.echoed_message
        last_reward = 0.0

        for step in range(1, MAX_STEPS + 1):
            if result.done:
                break

            message = get_model_message(client, step, last_echoed, last_reward, history)

            result = await env.step(MyEnvV4Action(message=message))
            obs = result.observation

            reward = result.reward or 0.0
            done = result.done
            error = None

            rewards.append(reward)
            steps_taken = step
            last_echoed = obs.echoed_message
            last_reward = reward

            log_step(step=step, action=message, reward=reward, done=done, error=error)

            history.append(f"Step {step}: {message!r} -> reward {reward:+.2f}")

            if done:
                break

        score = sum(rewards) / MAX_TOTAL_REWARD if MAX_TOTAL_REWARD > 0 else 0.0
        score = min(max(score, 0.0), 1.0)  # clamp to [0, 1]
        success = score >= SUCCESS_SCORE_THRESHOLD

    finally:
        try:
            await env.close()
        except Exception as e:
            print(f"[DEBUG] env.close() error (container cleanup): {e}", flush=True)
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


if __name__ == "__main__":
    asyncio.run(main())

Pre-Submission Checklist  — all must pass or you're disqualified

HF Space deploys

Automated ping to the Space URL — must return 200 and respond to reset()

OpenEnv spec compliance

Validate openenv.yaml, typed models, step()/reset()/state() endpoints

Dockerfile builds

Automated docker build on the submitted repo

Baseline reproduces

Run the submitted inference script — must complete without error and produce scores

3+ tasks with graders

Enumerate tasks, run each grader, verify scores/reward in 0.0–1.0 range

Mandatory Additional Instructions

Before submitting, ensure the following variables are defined in your environment configuration:

API_BASE_URL   The API endpoint for the LLM.

MODEL_NAME     The model identifier to use for inference.

HF_TOKEN       Your Hugging Face / API key.

The inference script must be named `inference.py` and placed in the root directory of the project

Participants must use OpenAI Client for all LLM calls using above variables

Participants must emit structured stdout logs strictly following the [START], [STEP], and [END] format defined in the sample inference.py provided below. Any deviation in field names, ordering, or formatting will result in incorrect evaluation scoring. Refer to the Sample Inference Script for the complete format specification and examples.

Infra Restrictions

Runtime of inference script should be less than 20min 

Make sure your env and inference can run on a machine with vcpu=2, memory=8gb

Validator

Run the pre-submission validation script before submitting



## Mandatory Implementation Rules

### Environment Variables (MUST be used exactly like this)

```python
API_BASE_URL = os.getenv("API_BASE_URL", "<default_allowed>")
MODEL_NAME = os.getenv("MODEL_NAME", "<default_allowed>")
HF_TOKEN = os.getenv("HF_TOKEN")