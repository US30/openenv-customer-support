import asyncio
import os
import json
from client import CustomerSupportEnv
from models import CustomerSupportAction

async def main():
    os.environ["TASK_NAME"] = "task1"
    env = CustomerSupportEnv(base_url="http://localhost:8001")
    res = await env.reset()
    print("RESET RESULT:", res)
    
    action = CustomerSupportAction(action_type="assign", department="TechSupport", priority="High")
    res = await env.step(action)
    print("STEP RESULT:", res)

asyncio.run(main())
