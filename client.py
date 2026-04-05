from typing import Dict
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State
from openenv.core import EnvClient
from models import CustomerSupportAction, CustomerSupportObservation

class CustomerSupportEnv(EnvClient[CustomerSupportAction, CustomerSupportObservation, State]):
    def _step_payload(self, action: CustomerSupportAction) -> Dict:
        return {
            "action_type": action.action_type,
            "department": action.department,
            "priority": action.priority,
            "reply_text": action.reply_text,
            "escalation_reason": action.escalation_reason,
        }

    def _parse_result(self, payload: Dict) -> StepResult[CustomerSupportObservation]:
        obs_data = payload.get("observation", {})
        metadata = obs_data.get("metadata", {})
        
        observation = CustomerSupportObservation(
            active_ticket_id=obs_data.get("active_ticket_id"),
            ticket_content=obs_data.get("ticket_content"),
            ticket_metadata=obs_data.get("ticket_metadata", {}),
            unresolved_count=obs_data.get("unresolved_count", 0),
            available_departments=obs_data.get("available_departments", []),
            available_priorities=obs_data.get("available_priorities", []),
            step_count=obs_data.get("step_count", 0),
            tickets_summary=obs_data.get("tickets_summary", []),
            metadata=metadata
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False)
        )

    def _parse_state(self, payload: Dict) -> State:
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
