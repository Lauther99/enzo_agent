from typing import Callable, Any, Dict
from abc import ABC, abstractmethod
import datetime
from typing import Any, Dict, Type
import uuid
import re
import inspect

authorized_types = {
    "<class 'str'>": "string",
    "<class 'int'>": "integer",
    "<class 'float'>": "number",
    "<class 'bool'>": "boolean",
    "<class 'list'>": "array",
    "typing.Optional[str]": "Optional[string]",
    "typing.Optional[int]": "Optional[integer]",
    "typing.Optional[float]": "Optional[number]",
    "typing.Optional[bool]": "Optional[boolean]",
    "typing.Optional[list]": "Optional[array]",
    "None": "null",  # Para funciones que retornan `None`
}


class BaseTool:
    def __init__(self, func: Callable[..., Any]):
        self.name = func.__name__  # Nombre de la función

        self.description = self._get_description(func)  # Documentación de la función
        self.inputs = self._extract_inputs(func)  # Tipos y descripciones de entrada

        return_type = func.__annotations__.get(
            "return", type(None)
        )  # Tipo de retorno o `NoneType`
        self.output_type: str = authorized_types.get(
            return_type
        )  # Mapeo o "unknown" si no está definido
        self._func = func  # Referencia a la función decorada

    def _get_description(self, func: Callable[..., Any]):
        description = func.__doc__.split("Args")[0].strip() if func.__doc__ else ""
        if description:
            return description
        else:
            raise ValueError(
                "The provided function does not have a valid description in its docstring."
            )

    def _extract_inputs(self, func: Callable[..., Any]) -> Dict[str, Dict[str, str]]:
        """Extrae tipos y descripciones de los argumentos de la función."""
        inputs = {}
        # Obtener el docstring de la función
        docstring = func.__doc__ or ""
        arg_descriptions = self._parse_arg_descriptions(docstring)

        # Obtener los parámetros de la función
        signature = inspect.signature(func)

        for param_name, param in signature.parameters.items():
            if param_name == "self" or param_name == "cls" or param_name == "kwargs":
                continue  # Ignorar 'self' y 'cls' para métodos de clase

            # Obtener el tipo del argumento
            param_type = (
                param.annotation if param.annotation is not param.empty else None
            )
            param_type_str = authorized_types.get(str(param_type), None)

            if not param_type or not param_type_str:
                raise ValueError(
                    f"Not supported '{param_type_str}' type for '{param_name}'. Only supported: {", ".join([item for _, item in authorized_types.items()])}."
                )

            # Obtener la descripción del argumento, si está en el docstring
            description = arg_descriptions.get(param_name, None)
            if not description:
                raise ValueError(f"Not valid description for '{param_name}'.")

            # Agregar al diccionario de inputs
            if param_name != "kwargs":
                inputs[param_name] = {
                    "type": param_type_str,
                    "description": description,
                }
        return inputs

    @staticmethod
    def _parse_arg_descriptions(docstring: str) -> Dict[str, str]:
        """Extrae descripciones de argumentos desde el docstring."""
        descriptions = {}
        args_section = re.search(r"Args:\s*(.*)", docstring, re.DOTALL)
        pattern = re.compile(r"^\s*(\w+):\s*(.+)$", re.MULTILINE)

        if args_section:
            args_text = args_section.group(1)
            matches = pattern.findall(args_text)
            for arg_name, description in matches:
                if description.strip():
                    descriptions[arg_name] = description.strip()
                else:
                    raise ValueError(f"Not valid description for '{arg_name}'.")

        return descriptions

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)  # Llama a la función decorada


def set_action(func: Callable[..., Any]) -> BaseTool:
    return BaseTool(func)


class BaseToolResponse:
    def __init__(
        self,
        call_id: uuid.UUID | str,
        tool_name: str,
        tool_response: list[dict],
        tool_friendly_response: list[dict],
        response_type: Type,
        llm_responses: list[str] = [],
        usage: dict[str, any] = {},
        metadata: dict[str, any] = {},
    ):
        self.call_id: uuid.UUID | str = call_id
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
            f"tool_name='{self.tool_name}', "
            f"tool_friendly_response='{self.tool_friendly_response}', "
            f"tool_response=[...], "
            f"response_type={self.response_type.__name__}, "
            f"llm_responses={self.llm_responses}, "
            f"date={self.date}, "
            f"usage={self.usage}, "
            f"metadata={self.metadata})"
        )


class BaseToolCollector(ABC):
    def __init__(self):
        self.ToolResponse: BaseToolResponse = None
        self.llm_responses: list[str] = []

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
