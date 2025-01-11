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
        self.description = func.__doc__  # Documentación de la función
        self.name = func.__name__  # Nombre de la función
        self.inputs = self._extract_inputs(func)  # Tipos y descripciones de entrada
        return_type = func.__annotations__.get('return', type(None))  # Tipo de retorno o `NoneType`
        self.output_type: str = authorized_types.get(return_type, "unknown")  # Mapeo o "unknown" si no está definido
        self._func = func  # Referencia a la función decorada

    # def _extract_inputs(self, func: Callable[..., Any]) -> Dict[str, Dict[str, str]]:
    #     """Extrae tipos y descripciones de los argumentos de la función."""
    #     inputs = {}
    #     # Parsear el docstring para obtener descripciones de los argumentos
    #     docstring = func.__doc__ or ""
    #     arg_descriptions = self._parse_arg_descriptions(docstring)

    #     for arg, arg_type in func.__annotations__.items():
    #         if arg == "return":
    #             continue
    #         # Construir la entrada enriquecida
    #         inputs[arg] = {
    #             "type": authorized_types.get(arg_type, "unknown"),
    #             "description": arg_descriptions.get(arg, "No description available.")
    #         }
    #     return inputs
    def _extract_inputs(self, func: Callable[..., Any]) -> Dict[str, Dict[str, str]]:
        """Extrae tipos y descripciones de los argumentos de la función."""
        inputs = {}
        # Obtener el docstring de la función
        docstring = func.__doc__ or ""
        arg_descriptions = self._parse_arg_descriptions(docstring)

        # Obtener los parámetros de la función
        signature = inspect.signature(func)
        for param_name, param in signature.parameters.items():
            if param_name == "self" or param_name == "cls":
                continue  # Ignorar 'self' y 'cls' para métodos de clase

            # Obtener el tipo del argumento
            param_type = param.annotation if param.annotation is not param.empty else "unknown"
            param_type_str = authorized_types.get(str(param_type), "unknown")

            # Obtener la descripción del argumento, si está en el docstring
            description = arg_descriptions.get(param_name, "No description available.")
            
            # Agregar al diccionario de inputs
            inputs[param_name] = {
                "type": param_type_str,
                "description": description
            }
        return inputs


    @staticmethod
    def _parse_arg_descriptions(docstring: str) -> Dict[str, str]:
        """Extrae descripciones de argumentos desde el docstring."""
        descriptions ={}
        args_section = re.search(r"Args:\s*(.*)", docstring, re.DOTALL)
        pattern = re.compile(r"^\s*(\w+):\s*(.+)$", re.MULTILINE)

        if args_section:
            args_text = args_section.group(1)
            matches = pattern.findall(args_text)
            for arg_name, description in matches:
                descriptions[arg_name] = description.strip()
        
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

    @abstractmethod
    def add_tool_response(
        self,
        call_id: uuid.UUID | str,
        tool_name: str,
        response: any,
        response_type: type,
        llm_responses: list[str] = [],
    ):
        pass