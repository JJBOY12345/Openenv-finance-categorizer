# Product Experimentation Branch

This branch represents an exploratory effort to turn the core reasoning engine into a **user-facing financial tool**. 

## Objective

We want to test if the strict `finance_env` grading mechanics and category matrices can be hooked up directly to a standard web frontend where users upload their messy bank statements (CSVs) and receive a nicely categorized budget ledger back.

## Important Constraints

- **Do Not Modify the Core Environment**: The `finance_env` directory must remain isolated and pure. It is an evaluator engine, not a web server.
- **API Wrapper**: We achieve this product flow by wrapping the existing env with a `product_server.py` that translates raw user CSVs into OpenEnv step formats, runs the agent inference internally, and converts the resulting state block back into a user-friendly JSON/CSV export.
