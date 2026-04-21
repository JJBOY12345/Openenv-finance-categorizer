# Hackathon & Competition Adaptations

This branch abstracts the core environment logic to support rapid, plug-and-play **domain swapping**. It prepares the evaluation engine to be reused natively in future hackathons or competitions without needing a ground-up rebuild.

## The Domain Abstraction Concept

Instead of hardcoding "finance" concepts (ledgers, merchants, budget categories), we introduce a `DomainProfile`. A domain defines three core components:

1. **Taxonomy (Action Space)**: The specific enum of valid categories for the task (e.g., medical diagnoses, code review severities).
2. **Dataset (Observation Space)**: The shape of the raw items needing processing (e.g., patient symptom logs, GitHub issue dumps).
3. **Grading Rubric**: The weighting applied to correct mappings and standard penalties.

## Available Domain Stubs

- **`finance/`**: The original transactional categorization dataset.
- **`medical/`**: A stub framework mapping patient symptom text blocks to diagnostic triage groupings.

## How to Spin Up a New Domain (WIP)

To adapt the engine for a new domain:
1. Create a subfolder in `domains/` (e.g., `resume_screening/`).
2. Provide a configuration schema declaring the new Pydantic target observation variables.
3. Replace the `finance_target_dataset.json` with your domain constraints.
The underlying `openenv` Step and State loop will natively inherit and execute those constraints safely.
