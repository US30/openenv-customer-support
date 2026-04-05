---
title: Customer Support Triage
emoji: 🎧
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 8000
pinned: false
---

# Customer Support Triage Environment

A real-world OpenEnv environment for the OpenEnv Hackathon. It simulates a Customer Support Triage system where an AI agent reads inbound support tickets and decides how to handle each one correctly.

## Environment Description

The agent reads one ticket at a time from an inbox and must choose the correct triage action. Tickets span categories like password resets, billing issues, churn risk, security vulnerabilities, and vague complaints.

### Action Space

| Action | Required Fields | When to Use |
|---|---|---|
| `assign` | `department`, `priority` | Route clear tickets to the correct department |
| `ask_user` | `reply_text` | Request more info for vague/ambiguous tickets |
| `escalate` | — | Handle critical churn or security tickets immediately |

**Available departments:** `TechSupport`, `Billing`, `Sales`, `Retention`  
**Available priorities:** `Low`, `Medium`, `High`, `Urgent`

### Observation Space

Each step returns:
- `active_ticket_id`: ID of the current ticket
- `ticket_content`: Full text of the ticket
- `ticket_metadata`: Dict with ticket `type`
- `unresolved_count`: Number of remaining open tickets
- `tickets_summary`: Summary list of all tickets and their statuses
- `reward`: Reward from the last action (0.0 or 1.0)
- `done`: Whether the episode has ended

### Reward Function

- **+1.0** for each correctly handled ticket (right department, right escalation, or right ask_user)
- **+0.0** for incorrect routing
- Final score = `sum(rewards) / total_tickets` (clipped to [0.0, 1.0])

## Task Difficulties

| Task | Difficulty | Tickets | Description |
|---|---|---|---|
| `task1` | Easy | 1 | Route a single password reset ticket to TechSupport |
| `task2` | Medium | 3 | Route a billing ticket, a password ticket, and one vague ticket requiring `ask_user` |
| `task3` | Hard | 5 | Mixed inbox: password reset, churn threat, security bypass, billing overcharge, sales inquiry |

## Setup & Usage

### Prerequisites

```bash
pip install openenv-core fastapi uvicorn pydantic openai
```

### Run locally

```bash
# 1. Start the environment server
uvicorn server.app:app --host 0.0.0.0 --port 8000

# 2. Set API credentials
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o-mini"
export HF_TOKEN="<your-openai-or-hf-api-key>"

# 3. Run the baseline inference script
python inference.py
```

### Run with Docker

```bash
docker build -t customer-support-env .
docker run -p 8000:8000 customer-support-env

# Then in another terminal:
LOCAL_IMAGE_NAME=customer-support-env python inference.py
```

## Baseline Results

Tested with `gpt-4o-mini` via `api.openai.com/v1`:

| Task | Steps | Score |
|---|---|---|
| task1 | 1 | 1.000 |
| task2 | 3 | 1.000 |
| task3 | 5 | 1.000 |

The environment is fully deterministic with unambiguous grading — the correct action for every ticket type is uniquely defined, making it suitable for reproducible RL benchmarking.

## Project Structure

```
customer_support_env/
├── inference.py          # Baseline inference script (mandatory)
├── client.py             # OpenEnv WebSocket client
├── models.py             # Pydantic Action & Observation models
├── openenv.yaml          # OpenEnv spec config
├── pyproject.toml        # Environment packaging spec
├── uv.lock               # Dependency lock file
├── validate-submission.sh # Validation script
├── Dockerfile            # Container definition
├── server/
│   ├── app.py            # FastAPI app wrapping the environment
│   └── environment.py    # Core environment logic & grader
└── README.md
```
