#!/usr/bin/env python3
import asyncio
import os
import textwrap
import json
from typing import List, Optional

from openai import OpenAI

from client import CustomerSupportEnv
from models import CustomerSupportAction

LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")
HF_TOKEN = os.getenv("HF_TOKEN")
API_KEY = HF_TOKEN or os.getenv("OPENAI_API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
BENCHMARK = "customer_support"
MAX_STEPS = 10
TEMPERATURE = 0.5
MAX_TOKENS = 150
SUCCESS_SCORE_THRESHOLD = 0.5

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are an AI customer support agent. You must act on the currently active ticket.
    Your available actions are:
    1. assign: requires 'department' (e.g. TechSupport, Billing, Sales, Retention) and optionally 'priority' (Low, Medium, High, Urgent).
    2. ask_user: requires 'reply_text' to ask the user for more info.
    3. escalate: escalates a critical/churn ticket.

    You must reply ONLY with a valid JSON object matching the action schema. DO NOT wrap the json in backticks or markdown, just return raw JSON.
    Example:
    {"action_type": "assign", "department": "TechSupport", "priority": "High"}
    {"action_type": "ask_user", "reply_text": "What is your OS?"}
    {"action_type": "escalate"}
    """
).strip()

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

def build_user_prompt(step: int, obs: dict, history: List[str]) -> str:
    history_block = "\n".join(history[-3:]) if history else "None"
    return textwrap.dedent(
        f"""
        Step: {step}
        Active Ticket:
        Content: {obs.get("ticket_content")}
        Metadata: {obs.get("ticket_metadata")}
        
        Available Departments: {obs.get("available_departments")}
        Available Priorities: {obs.get("available_priorities")}
        
        Previous actions:
        {history_block}
        
        Provide the next action as JSON.
        """
    ).strip()

def get_model_action(client: OpenAI, step: int, obs: dict, history: List[str]) -> tuple:
    user_prompt = build_user_prompt(step, obs, history)
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()
        if text.startswith("```json"): text = text[7:]
        if text.endswith("```"): text = text[:-3]
        text = text.strip()
        data = json.loads(text)
        return CustomerSupportAction(**data), text
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return CustomerSupportAction(action_type="assign", department="TechSupport", priority="Low"), "{}"

async def run_task(task_name: str):
    # Set env var so the server picks up the correct task logic on instantiation if running locally in docker
    os.environ["TASK_NAME"] = task_name 
    
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    
    if LOCAL_IMAGE_NAME:
        env = await CustomerSupportEnv.from_docker_image(LOCAL_IMAGE_NAME, env_vars={"PORT": "8000", "TASK_NAME": task_name})
    else:
        env = CustomerSupportEnv(base_url="http://localhost:8000")
        
    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    success = False

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)
    score = 0.0

    try:
        # Since local HTTP server might not use task_name passed via env well unless restarted, we explicitly set it via kwargs or rely on env
        result = await env.reset(task_name=task_name)
        obs = result.observation
        
        for step in range(1, MAX_STEPS + 1):
            if result.done:
                break
                
            # Serialize observation for prompt
            obs_dict = {
                "ticket_content": obs.ticket_content,
                "ticket_metadata": obs.ticket_metadata,
                "available_departments": obs.available_departments,
                "available_priorities": obs.available_priorities,
            }
                
            action_obj, raw_text = get_model_action(client, step, obs_dict, history)
            
            result = await env.step(action_obj)
            obs = result.observation
            
            reward = result.reward or 0.0
            done = result.done
            
            rewards.append(reward)
            steps_taken = step
            
            safe_action_text = raw_text.replace('\n', ' ').replace('\r', '')
            log_step(step=step, action=safe_action_text, reward=reward, done=done, error=None)
            
            history.append(f"Step {step} action: {safe_action_text} -> reward {reward}")
            
            if done:
                break
                
        MAX_TOTAL_REWARD = max(float(len(obs.tickets_summary)), 1.0)
        score = sum(rewards) / MAX_TOTAL_REWARD
        score = min(max(score, 0.01), 0.99)  # Strictly within (0, 1) per hackathon spec
        success = score >= SUCCESS_SCORE_THRESHOLD

    except Exception as e:
        print(f"[DEBUG] Error during run: {e}")
        score = 0.01  # Strictly > 0.0 per hackathon spec
        success = False
    finally:
        try:
            await env.close()
        except:
            pass
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

async def main():
    tasks = ["task1", "task2", "task3"]
    from threading import Thread
    import uvicorn
    import time
    from server.app import app
    
    server_thread = None
    if not LOCAL_IMAGE_NAME:
        print("[DEBUG] Starting local server for testing...")
        server_thread = Thread(target=uvicorn.run, args=(app,), kwargs={"host":"0.0.0.0", "port":8000, "log_level":"error"}, daemon=True)
        server_thread.start()
        time.sleep(2) # wait for boot
        
    for t in tasks:
        # HTTP calls stateless routing, we use task configured on env side if possible.
        # Note: If running a shared persistent server, using os.environ might not be thread safe or apply to the already running server. 
        # A workaround is restarting server, but we will assume single-run tests for bash script.
        # Usually HF Spaces run tasks sequentially or expect env to read state.
        # But wait, openenv `reset` doesn't pass task config easily without query params.
        await run_task(t)

if __name__ == "__main__":
    asyncio.run(main())
