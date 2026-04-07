import hashlib
import os
import uuid
from typing import List, Dict, Optional

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

# Ensure relative imports resolve correctly based on execution context
try:
    from models import CustomerSupportAction, CustomerSupportObservation
except ImportError:
    from ..models import CustomerSupportAction, CustomerSupportObservation

TASKS = {
    "task1": [
        {"id": "t1", "content": "I forgot my password and cannot log into my account. Help!", "type": "password"}
    ],
    "task2": [
        {"id": "t2_1", "content": "How do I update my billing email?", "type": "billing"},
        {"id": "t2_2", "content": "The system says invalid credentials.", "type": "password"},
        {"id": "t2_3", "content": "My app crashed!", "type": "vague"}
    ],
    "task3": [
        {"id": "t3_1", "content": "How to change password?", "type": "password"},
        {"id": "t3_2", "content": "I want an immediate refund, this is garbage! Cancel my account!", "type": "churn"},
        {"id": "t3_3", "content": "Found a way to bypass authentication on the user portal.", "type": "security"},
        {"id": "t3_4", "content": "Charge on my credit card is double what it should be.", "type": "billing"},
        {"id": "t3_5", "content": "Is there a student discount?", "type": "sales"}
    ]
}

class CustomerSupportEnvironment(Environment):
    """Customer Support Environment for testing RL agents."""
    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self, task_name: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self._session_id = str(uuid.uuid4())
        self._state = State(episode_id=self._session_id, step_count=0)
        
        # Priority: explicit arg -> env var -> default
        self.task_name = task_name if task_name else os.getenv("TASK_NAME", "task1")
        if self.task_name not in TASKS:
            self.task_name = "task1"
            
        self.tickets = []
        self._load_tickets()
        self.current_ticket_index = 0

    def _load_tickets(self):
        self.tickets = [dict(t) for t in TASKS[self.task_name]]
        for t in self.tickets:
            t["status"] = "open"

    def _get_active_ticket(self) -> Optional[Dict]:
        if self.current_ticket_index < len(self.tickets):
            return self.tickets[self.current_ticket_index]
        return None

    def reset(self, seed: Optional[int] = None, episode_id: Optional[str] = None, task_name: Optional[str] = None, **kwargs) -> CustomerSupportObservation:
        """Reset the environment."""
        if episode_id is not None:
            self._session_id = episode_id
        
        if task_name is not None and task_name in TASKS:
            self.task_name = task_name
            
        self._state = State(episode_id=self._session_id, step_count=0)
        self._load_tickets()
        self.current_ticket_index = 0
        
        return self._make_observation(reward=0.01, done=False)

    def _make_observation(self, reward: float = 0.0, done: bool = False) -> CustomerSupportObservation:
        t = self._get_active_ticket()
        unresolved = sum(1 for x in self.tickets if x["status"] == "open")
        summary = [{"id": x["id"], "summary": x["content"][:30] + "...", "status": x["status"]} for x in self.tickets]
        
        return CustomerSupportObservation(
            active_ticket_id=t["id"] if t else None,
            ticket_content=t["content"] if t else None,
            ticket_metadata={"type": t["type"]} if t else {},
            unresolved_count=unresolved,
            step_count=self._state.step_count,
            tickets_summary=summary,
            reward=float(reward),
            done=done
        )

    def step(self, action: CustomerSupportAction, timeout_s: Optional[float] = None, **kwargs) -> CustomerSupportObservation:
        """Execute action step."""
        self._state.step_count += 1
        t = self._get_active_ticket()
        
        if not t:
            return self._make_observation(reward=0.05, done=True)
            
        action_type = action.action_type.lower()
        ttype = t["type"]
        is_correct = False
        
        # Simple logical grader included inline for self-containment
        if ttype == "password":
            if action_type == "assign" and action.department == "TechSupport":
                is_correct = True
        elif ttype == "billing":
            if action_type == "assign" and action.department == "Billing":
                is_correct = True
        elif ttype == "sales":
            if action_type == "assign" and action.department == "Sales":
                is_correct = True
        elif ttype == "vague":
            if action_type == "ask_user":
                is_correct = True
        elif ttype == "churn":
            if action_type == "escalate":
                is_correct = True
        elif ttype == "security":
            if action_type == "escalate":
                is_correct = True
            elif action_type == "assign" and action.department == "TechSupport" and action.priority in ["High", "Urgent"]:
                is_correct = True

        if is_correct:
            reward = 0.95  # High reward but strictly < 1.0 per hackathon spec
            t["status"] = "resolved"
        else:
            reward = 0.05  # Low reward but strictly > 0.0 per hackathon spec
            t["status"] = "failed"

        self.current_ticket_index += 1
        done = self.current_ticket_index >= len(self.tickets)
        
        return self._make_observation(reward=reward, done=done)

    @property
    def state(self) -> State:
        return self._state
