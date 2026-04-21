# LLM Benchmarking Framework

This branch extends the core environment to evaluate and compare multiple state-of-the-art Large Language Models (LLMs) on structured financial reasoning tasks.

## Purpose

While the `main` branch establishes a single, reliable deterministic pipeline, this branch introduces an orchestration layer designed to cycle through multiple models concurrently or sequentially. The goal is to produce comparative metrics on structured schema adherence and logical reasoning accuracy.

## Planned Comparisons

We aim to test models including, but not limited to:
- GPT-4 / GPT-4o
- Claude 3.5 Sonnet
- Qwen 2.5
- Mistral Large

## Architecture

This branch builds directly upon the existing `finance_env`. It leaves the `state()`, `step()`, and `reset()` contracts fully intact. The only change is replacing the single-model `inference.py` loop with a multi-model iterator (`benchmark.py`) that aggregates the final episode statistics into comprehensive CSV/JSON reports.
