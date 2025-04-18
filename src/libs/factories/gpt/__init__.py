import typing as T # noqa

from src.libs.factories.gpt.base import BaseGPTClient
from src.libs.factories.gpt.mixins.generate_result import GenerateResultMixin
from src.libs.factories.gpt.mixins.generate_questions import GenerateQuestionsMixin
from src.libs.factories.gpt.mixins.generate_transcript import GenerateTranscriptMixin
from src.libs.http_client import HttpClient
from src.settings import GPTSettings


class GPTClient(
    GenerateResultMixin,
    GenerateQuestionsMixin,
    GenerateTranscriptMixin,
    BaseGPTClient
):
    def __init__(self, http_client: HttpClient, settings: GPTSettings):
        super().__init__(http_client, settings)
