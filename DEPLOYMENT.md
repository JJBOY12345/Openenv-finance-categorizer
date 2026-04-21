# Deployment & Infrastructure

The framework is packaged for portability, ensuring consistent benchmarks across local, CI/CD, and remote staging environments. 

## Docker Packaging

The repository uses a multistage `Dockerfile` to guarantee reproducibility:
- Based on `python:3.10-slim`.
- Leverages `uv` for lightning-fast, reproducible dependency resolution (via `uv.lock`).
- Configured to run reliably behind a standard `uvicorn` setup mapping to port `8000`.

### Local Build and Run
```bash
docker build -t finance_env_benchmark:latest .
docker run -p 8000:8000 finance_env_benchmark:latest
```

## Hugging Face Space Integration

The `main` branch natively supports deployment as a Hugging Face Space.

### Automatic Endpoint Registration

When pushed to a Space, the environment registers the following fully-compliant endpoints:

| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/health` | `GET` | Container readiness and system liveness probe. Returns `{"status":"healthy"}`. |
| `/reset` | `POST` | Initializes a new internal episode. Requires a `task_id`. Returns the initial observation. |
| `/step` | `POST` | Processes the given `FinanceAction`. Returns a tuple of `(Observation, Reward, Done, Info)`. |
| `/state` | `GET` | Bypasses the active observation view to dump the entire secure environment memory for the grader. |

### CI/CD Deployment Flow

```bash
# Register the target Space
git remote add space https://huggingface.co/spaces/<your_username>/finance_env

# Sync to Hub
git push space main
```

This setup enables rapid swapping of benchmarks or models without concerning oneself with the underlying host OS or Python configuration matrix.
