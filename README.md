---
title: Finance Env Environment Server
emoji: 🎬
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
app_port: 8000
base_path: /web
tags:
  - openenv
---

# Finance Transaction Categorizer Environment

This is a production-quality OpenEnv environment built for the Meta PyTorch OpenEnv Hackathon. It simulates a real-world **personal finance workflow** where a user (or agent) is given messy bank and credit-card transactions and must categorize them to build an accurate budgeting ledger.

## 1. Domain & Motivation

Transactions often have ambiguous merchant names, require determining context (e.g., separating an outgoing Zelle expense from an incoming Zelle transfer, or separating a fee from a purchase), and feature misleading memos. 

Unlike toy games, budgeting and bookkeeping are massive, repeated consumer pain points. This environment grounds RL or agent actions in structured financial data, presenting a practical task with strict deterministic evaluation.

## 2. Tasks & Difficulties

The environment provides 3 built-in tasks of escalating difficulty, selected via `task_id` during `reset()`.

| Task ID | Difficulty | Characteristics |
| :--- | :--- | :--- |
| `easy_budget_cleanup_v1` | **Easy** | Obvious everyday merchants, minimal ambiguity, clear category mappings (e.g. `supermarket` -> `groceries`). |
| `medium_ambiguous_ledger_v1` | **Medium** | Ambiguous merchants, transfer vs. expense confusion, and subscription vs. shopping confusion. |
| `hard_operational_ledger_v1` | **Hard** | Highly similar merchant string matches requiring exact operational reading, fee classification, and nuanced transfer flow discernment. |

## 3. Usage & Setup

### Requirements
- Docker
- Python 3.10+
- `openenv-core` package

### Local Check / Start
We use the OpenEnv Python standard class logic.

```bash
uv sync   # or pip install -e .
```

To run the environment visually via the OpenEnv built-in dashboard:
```bash
# Verify it passes constraints
openenv validate

# Run locally
uvicorn finance_env.server.app:app --reload
# Then navigate to your localhost port or connect natively via scripts
```

### Docker
```bash
docker build -t finance_env:latest .
docker run -p 8000:8000 finance_env:latest
```

## 4. Models (Observation & Actions)

The environment follows the strict OpenEnv Spec Pydantic schema structure. Note that **answer keys are strictly protected** and never exposed dynamically to the observation.

### Action Space (`FinanceAction`)
Agents pass an action object containing their target directive and payload.
Currently supported actions:
- **`categorize_transaction`**: Pick one of the 14 defined budget categories for a given `transaction_id`.
- **`finalize`**: Mark the episode as finished. A premature finalize implies low task completion and is penalized.

### Observation Space (`FinanceObservation`)
Exposes:
- `task_description`: Natural text explanation of the agent's goal.
- `allowed_actions`: Array of permitted action types.
- `unresolved_transactions`: A list of remaining transactions. Includes `transaction_id`, `merchant`, `amount`, `currency`, `posted_date`, `memo`. 
- `processed_entries`: Summary of already mapped transactions.
- `alerts` & `action_history`: Context window for warnings and previous step memory.

## 5. Baseline Evaluation

The repository includes a configured, root-level `inference.py` script. This script establishes the required strict integration format and serves as the primary inference method.

### Contract Compliance
The script uses the **OpenAI Python Client** instantiated with the environment variables `API_BASE_URL`, `MODEL_NAME`, and `HF_TOKEN`.

It correctly partitions deterministic structured JSON logging (outputting **only** the `[START]`, `[STEP]`, and `[END]` tags to standard output to guarantee `grep` / evaluator capture) from unstructured warnings/failed model parses (logged strictly to standard error).

### Running It
```bash
# Set your environment details. Ex. for HuggingFace Router:
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-7B-Instruct:together"
export HF_TOKEN="<your_token_here>"

# Execute baseline
python inference.py
```

### Baseline Status
* **Status:** Operational but Partial
* **Current Observations:** Deterministic fallback works properly, but on the `hard` task, certain LLM inference providers repeatedly suffer from intermittent request timeouts (`APIStatusError`). Failover logic catches this, but repeated stable scores currently depend heavily on the backend provider chosen. Complete full-credit deterministic checks via unit tests demonstrate the underlying validity of the environment logic regardless of the LLM wrapper used.

## 6. Hugging Face Deployment

This project is configured as a Hugging Face Docker Space. The root `README.md` handles the configuration, and the root `Dockerfile` defines the container.

### Git Deployment Steps
To deploy the code to a Space:

```bash
# Set up git remote for your Hugging Face Space (replace with your Space URL)
git remote add space https://huggingface.co/spaces/<your_username>/finance_env

# Push to deploy automatically on the Hugging Face hub
git push space main
```

### Endpoint Verification
Once deployed, the Space automatically builds and exposes standard OpenEnv HTTP endpoints:

1. **/health**: Verify container readiness.
   ```bash
   curl -X GET "https://<your_username>-finance-env.hf.space/health"
   # Expected Output: {"status":"healthy"}
   ```

2. **/reset**: Create an initial environment episode step.
   ```bash
   curl -X POST "https://<your_username>-finance-env.hf.space/reset" -H "Content-Type: application/json" -d "{}"
   # Expected Output: Valid FinanceObservation JSON payload.
   ```
