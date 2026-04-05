from typing import List, Dict, Optional
from openenv.core.env_server.types import Action, Observation

class CustomerSupportObservation(Observation):
    """Observation space for the Customer Support Triage environment."""
    active_ticket_id: Optional[str] = None
    ticket_content: Optional[str] = None
    ticket_metadata: Dict[str, str] = {}
    
    unresolved_count: int = 0
    available_departments: List[str] = ["TechSupport", "Billing", "Sales", "Retention"]
    available_priorities: List[str] = ["Low", "Medium", "High", "Urgent"]
    step_count: int = 0
    tickets_summary: List[Dict[str, str]] = []

class CustomerSupportAction(Action):
    """Action space for the Customer Support Triage environment."""
    action_type: str  # "assign", "ask_user", "escalate"
    department: Optional[str] = None
    priority: Optional[str] = None
    reply_text: Optional[str] = None
    escalation_reason: Optional[str] = None
