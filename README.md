# LLM Evaluation Framework: Structured Financial Reasoning

A deterministic, production-quality environment for evaluating Large Language Models on complex, structured financial reasoning tasks. 

This repository provides an OpenEnv-compliant ledger simulator designed to test an agent's ability to parse ambiguous data, categorize messy transactions, apply logic matrices, and survive multi-step execution flows without hallucinating schema boundaries.

## 🌟 Resume Highlights

- **Built a Deterministic Evaluation Engine:** Designed a high-fidelity environment simulating ledger operations with zero data leakage, enabling rigorous and reproducible benchmarking of LLMs.
- **Implemented Secure Grading:** Engineered isolated `state()` and `step()` functions where ground-truth answers are strictly firewall protected from the LLM context window.
- **Robust Inference Pipeline:** Created an error-resilient agent orchestrator using the OpenAI client that cleanly partitions structured logging outputs (`stdout`) from trace errors (`stderr`).
- **Production Infrastructure:** Fully Dockerized the environment with optimized `uv` dependency locking, allowing native CI/CD deployments directly to Hugging Face Spaces.

## 📖 Documentation Directory

- **[Architecture & Design](ARCHITECTURE.md)**: Details on the state machine, typed action/observation Pydantic models, and the `inference.py` orchestrator architecture.
- **[Evaluation & Grading](EVALUATION.md)**: Explanation of the deterministic grading philosophy, lack of prompt "leakage", and the difficulty tiers.
- **[Deployment Guide](DEPLOYMENT.md)**: Instructions for running the Docker containers or deploying the endpoints.
- **[Development History](docs/development_history/)**: Archive of early planning and architecture decisions.

## 🚀 Quick Start (Local Run)

You will need Python 3.10+ and the `openenv-core` package.

### 1. Installation

```bash
# We highly recommend using `uv` for exact lockfile synchronization
uv sync

# Or pip fallback
pip install -e .
```

### 2. Verify Specs

The environment strictly adheres to OpenEnv standards. Validate the schema contracts:
```bash
openenv validate
```

### 3. Run the Inference Baseline

The framework uses an `inference.py` script. Set your target API credentials and run a benchmark test:

```bash
# Example testing against a Together/HF Router hosted model
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-7B-Instruct:together"
export HF_TOKEN="<your_token_here>"

python inference.py
```

*Note: The script outputs strict JSON step details to standard out, while runtime errors or model retries are isolated entirely to standard error.*
