import uuid
from typing import Any, Type
import datetime

class BaseToolResponse:
    def __init__(
        self,
        call_id: uuid.UUID | str,
        # scratchpad_id: uuid.UUID | str | None,
        tool_name: str,
        tool_response: list[dict],
        tool_friendly_response: list[dict],
        response_type: Type,
        llm_responses: list[str] = [],
        usage: dict[str, any] = {},
        metadata: dict[str, any] = {},
    ):
        self.call_id: uuid.UUID | str = call_id
        # self.scratchpad_id: uuid.UUID | str | None = scratchpad_id
        self.tool_name: str = tool_name
        self.tool_friendly_response: list[dict] = tool_friendly_response
        self.tool_response: list[dict] = tool_response
        self.response_type: Type = response_type
        self.llm_responses: list[str] = llm_responses
        self.date = datetime.datetime.now().isoformat()
        self.usage = usage
        self.metadata = metadata

    def to_dict(self):
        return {
            "call_id": str(self.call_id),
            # "scratchpad_id": str(self.scratchpad_id),
            "tool_name": self.tool_name,
            "tool_response": self.tool_response,
            "tool_friendly_response": self.tool_friendly_response,
            "response_type": getattr(
                self.response_type, "__name__", str(self.response_type)
            ),
            "llm_responses": self.llm_responses,
            "date": self.date,
            "usage": self.usage,
            "metadata": self.metadata,
        }

    def __repr__(self):
        return (
            f"BaseToolResponse("
            f"call_id={self.call_id}, "
            # f"scratchpad_id={self.scratchpad_id}, "
            f"tool_name='{self.tool_name}', "
            f"tool_friendly_response='{self.tool_friendly_response}', "
            f"tool_response=[...], "
            f"response_type={self.response_type.__name__}, "
            f"llm_responses={self.llm_responses}, "
            f"date={self.date}, "
            f"usage={self.usage}, "
            f"metadata={self.metadata})"
        )

class Base_LLM_Response:
    def __init__(
        self,
        *,
        type: str,
        messages_list: list,
        llm_response: str,
        formated_response: any,
        model_name: str,
        llm_call_id,
        usage: dict
    ):
        self.type = type
        self.messages_list = messages_list
        self.llm_response = llm_response
        self.formated_response = formated_response
        self.model_name = model_name
        self.llm_call_id = llm_call_id
        self.usage = usage
        self.date = datetime.datetime.now().isoformat()

    def __repr__(self):
        return (
            f"Base_LLM_Response(\n"
            f"    type={repr(self.type)},\n"
            f"    llm_call_id={repr(self.llm_call_id)},\n"
            f"    model_name={repr(self.model_name)},\n"
            f"    messages_list={repr(self.messages_list)},\n"
            f"    llm_response={repr(self.llm_response)},\n"
            f"    formated_response={repr(self.formated_response)}\n"
            f"    date={repr(self.date)}\n"
            f"    usage={repr(self.usage)},\n"
            f")"
        )

    def to_dict(self):
        return {
            "type": self.type,
            "llm_call_id": self.llm_call_id,
            "model_name": self.model_name,
            "messages_list": self.messages_list,
            "llm_response": self.llm_response,
            "formated_response": self.formated_response,
            "date": self.date,
            "usage": self.usage,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            type=data.get("type"),
            llm_call_id=data.get("llm_call_id"),
            model_name=data.get("model_name"),
            messages_list=data.get("messages_list", []),
            llm_response=data.get("llm_response"),
            formated_response=data.get("formated_response"),
            date=data.get("date"),
            usage=data.get("usage", {}),
        )

class Base_Agent_Response:
    def __init__(
        self,
        thought: str | None=None,
        action: str | None=None,
        parameters: Any | None = None,
        final_answer: str | None=None,
        markdown_info: str | None=None,
        content: str | None=None,
        usage: str | None=None,
        llm_call_id: str | None=None,
    ):
        self.thought = thought
        self.action = action
        self.parameters = parameters
        self.final_answer = final_answer
        self.markdown_info = markdown_info
        self.content = content
        self.usage = usage
        self.llm_call_id = llm_call_id
        
    def to_dict(self):
        return {
            "thought": self.thought,
            "action": self.action,
            "parameters": self.parameters,
            "final_answer": self.final_answer,
            "markdown_info": self.markdown_info,
            "content": self.content,
            "usage": self.usage,
            "llm_call_id": self.llm_call_id,
        }
    

