import logging
from typing import Any
from src.components.prompt import ChatTemplate
from openai import OpenAI
import time
import math
from src.settings.settings import Config
from abc import ABC, abstractmethod
from typing import Any
from typing import Generator


class BaseLLM(ABC):
    def __init__(self, api_key=None, base_url=None):
        self.api_key = api_key
        self.base_url = base_url
        self.default_model_name = ""

    @abstractmethod
    def chat_llm(
        self,
        *,
        model_name: str | None = None,
        messages: ChatTemplate | None = None,
        max_tokens=700,
        temperature: float = 0.1,
        top_p: float = None,
        seed: int = None,
        extra_headers: dict[str:Any] = {},
        has_stream=False,
        **kwargs,
    ) -> Generator[
        tuple[None, None, dict[str, int]]
        | tuple[None, None, dict[str, Any]]
        | tuple[str | None, None, None]
        | tuple[str, None, dict[str, int]]
        | tuple[None, list, dict[str, Any]],
        Any,
        None,
    ]:
        pass


class GenericLLM:

    @staticmethod
    def from_openai(api_key):
        """For agents or complicated tasks"""
        model_name = "gpt4o-mini"
        return BaseGenericLLM(api_key=api_key, default_model_name=model_name)

    @staticmethod
    def from_groq_llama3_1_8b(api_key, use_cache=False):
        """For chill tasks"""
        model_name = "llama-3.1-8b-instant"
        base_url = "https://api.groq.com/openai/v1"
        default_headers = {"x-use-cache": "0" if not use_cache else "1"}

        return BaseGenericLLM(
            api_key=api_key,
            base_url=base_url,
            default_model_name=model_name,
            default_headers=default_headers,
        )

    @staticmethod
    def from_groq_llama3_3_70b(api_key, use_cache=False):
        """For agents or complicated tasks"""
        model_name = "llama-3.3-70b-versatile"
        base_url = "https://api.groq.com/openai/v1"
        default_headers = {"x-use-cache": "0" if not use_cache else "1"}

        return BaseGenericLLM(
            api_key=api_key,
            base_url=base_url,
            default_model_name=model_name,
            default_headers=default_headers,
        )

    @staticmethod
    def from_groq_whisper_large(api_key, use_cache=False):
        """For audio transcription complicated tasks"""
        model_name = "whisper-large-v3"
        base_url = "https://api.groq.com/openai/v1"
        default_headers = {"x-use-cache": "0" if not use_cache else "1"}

        return BaseGenericLLM(
            api_key=api_key,
            base_url=base_url,
            default_model_name=model_name,
            default_headers=default_headers,
        )
    
    @staticmethod
    def from_HF_llama3_3_70b_instruct(api_key, use_cache=False):
        """For agents or complicated tasks"""
        model_name = "meta-llama/Llama-3.3-70B-Instruct"
        base_url = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.3-70B-Instruct/v1"
        default_headers = {"x-use-cache": "0" if not use_cache else "1"}

        return BaseGenericLLM(
            api_key=api_key,
            base_url=base_url,
            default_model_name=model_name,
            default_headers=default_headers,
        )


class BaseGenericLLM(BaseLLM):
    def __init__(
        self, api_key, base_url=None, *, default_model_name, default_headers=None
    ) -> None:
        super().__init__(api_key, base_url)
        self.llm_client = OpenAI(api_key=api_key, base_url=base_url)
        self.default_model_name = default_model_name
        self.default_headers = default_headers or None

    def chat_llm(
        self,
        *,
        model_name: str | None = None,
        messages: ChatTemplate,
        max_tokens=700,
        temperature=0.1,
        top_p: float = None,
        seed: int = None,
        extra_headers: dict[str:Any] = {"x-use-cache": "0"},
        has_stream=False,
        **kwargs,
    ):
        stream_options = {"include_usage": True} if has_stream else None
        messages_list = [
            {
                "role": message.role if message.role != "tool" else "user",
                "content": message.content,
            }
            for message in messages.messages
        ]

        start_time = time.time()

        try:
            response = self.llm_client.chat.completions.create(
                model=model_name or self.default_model_name,
                messages=messages_list,
                temperature=temperature,
                top_p=top_p,
                seed=seed,
                max_tokens=max_tokens,
                extra_headers=extra_headers,
                stream=has_stream,
                stream_options=stream_options,
            )
            if has_stream:
                for chunk in response:
                    # HF + Openai
                    has_usage = chunk.usage is not None
                    has_choices = bool(chunk.choices)
                    if has_usage or not has_choices:
                        u = {
                            "input_tokens": chunk.usage.prompt_tokens,
                            "output_tokens": chunk.usage.completion_tokens,
                        }
                        yield None, None, u
                    # groq
                    elif hasattr(chunk, "x_groq"):
                        usage = chunk.x_groq.get("usage", {})
                        if usage:
                            u = {
                                "input_tokens": usage.get("prompt_tokens", 0),
                                "output_tokens": usage.get("completion_tokens", 0),
                            }
                            yield None, None, u
                    else:
                        content = chunk.choices[0].delta.content if has_choices else ""
                        yield content, None, None
            else:
                content = response.choices[0].message.content
                usage = {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                }

                yield content, messages_list, usage

        except Exception as e:
            logging.info(f"Error en la solicitud: {e}")
            content = f"<Answer>Error en la solicitud: {e}</Answer>"

            usage = {
                "input_tokens": BaseGenericLLM._get_tokens_quantity(messages_list),
                "output_tokens": 0,
            }
            yield content, None, usage

        finally:
            t2 = time.time()
            response_time = t2 - start_time
            time_usage = {
                "response_time": response_time,
                "model": model_name or self.default_model_name,
            }

            yield None, messages_list, time_usage

    def audio_transcription_llm(self, file_path: str, temperature: float = 0.1):

        try:
            with open(file_path, "rb") as audio_file:
                response = self.llm_client.audio.transcriptions.create(
                    model=self.default_model_name,
                    file=audio_file,
                    language=Config.LANGUAGE,
                    response_format="json",
                    temperature=temperature,
                    extra_headers={"x-use-cache": "0"},
                )

            return response.text

        except Exception as e:
            logging.error(f"Error en la solicitud: {e}")
            message = f"Hubo un error al procesar el audio: {str(e)}"

            return message

    @staticmethod
    def _get_tokens_quantity(messages_list: list[dict]):
        text = ""
        for item in messages_list:
            text += f"""{item["role"]}:\n{item["content"]}\n\n"""

        w = [char for char in text]
        return math.ceil(len(w) / 4)


GROQ_API_KEY = Config.GROQ_API_KEY
HF_API_KEY = Config.HF_TOKEN


default_llms = {
    "from_HF_llama3_3_70b_instruct": GenericLLM.from_HF_llama3_3_70b_instruct(HF_API_KEY),
    "from_groq_whisper_large": GenericLLM.from_groq_whisper_large(GROQ_API_KEY),
}