# Customer Support Triage Environment

This is a real-world task environment for the OpenEnv Hackathon. It models an Email Customer Support Triage system where an AI agent must route or respond to an inbox of highly varied tickets.

## Description

The agent reads one ticket at a time and chooses between 3 actions:
- `assign`: Assign the ticket to a department (`TechSupport`, `Billing`, `Sales`, `Retention`) with a priority.
- `ask_user`: Repty to the ticket asking for clarification if context is vague.
- `escalate`: Immediately escalate critical user issues (security or heavy churn risks).

## Setup & Usage

To validate the environment locally:
```bash
# 1. Start the server
uvicorn server.app:app --host 0.0.0.0 --port 8000

# 2. Export OpenAI variables
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export HF_TOKEN="<your token>"

# 3. Run the baseline
python inference.py
```

## Task Difficulties

- **task1 (Easy)**: Route a single obvious password reset ticket to Technical Support.
- **task2 (Medium)**: Route 3 tickets, identifying one vague ticket that requires returning an `ask_user` reply.
- **task3 (Hard)**: Route 5 tickets, accurately isolating an angry churn risk and a security bypass, properly applying `escalate` and `assign` respectively, without failing standard tickets.

## Baseline Metrics

The baseline model (Qwen 72B) typically scores between 0.8 to 1.0 reliably across all tasks, proving that the tasks are deterministic, properly graded, and fully adhere to [0.0, 1.0] scoring constraints via partial progress.
