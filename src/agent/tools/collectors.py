from typing import Type
import uuid

from src.components.tool import BaseToolCollector
from src.agent.types import BaseToolResponse

class Collector:
    def __init__(self):
        # self.AgentResponseCollector: AgentResponseCollector = AgentResponseCollector()
        # self.LLMResponseCollector: LLMResponseCollector = LLMResponseCollector()
        self.ToolsCollector: dict[str, BaseToolCollector] = {}
        self.last_call_id: str | None = None

    def add_tool_collector(
        self, new_collector: Type[BaseToolCollector], call_id: uuid.UUID | str
    ):
        self.ToolsCollector[call_id] = new_collector()

    def set_last_tool_call_id(self, call_id: uuid.UUID | str):
        self.last_call_id = call_id

    def get_last_tool_call_id(self):
        return self.last_call_id
    
    

class EmailScheduleToolCollector(BaseToolCollector):
    def __init__(self):
        super().__init__()

    def add_tool_response(
        self,
        call_id: uuid.UUID | str,
        tool_name: str,
        tool_response: list[dict],
        tool_friendly_response: list[dict],
        response_type: type,
        usage={},
        metadata={},
    ):
        self.ToolResponse = BaseToolResponse(
            call_id=call_id,
            tool_name=tool_name,
            tool_response=tool_response,
            tool_friendly_response=tool_friendly_response,
            response_type=response_type,
            llm_responses=self.llm_responses,
            usage=usage,
            metadata=metadata,
        )
        return self.ToolResponse

    def to_dict(self):
        return {
            "ToolResponse": self.ToolResponse.to_dict(),
        }

    def __repr__(self):
        return (
            f"UncertainityStatusToolCollector(\n"
            f"ToolResponse={self.ToolResponse!r},\n"
            f")"
        )