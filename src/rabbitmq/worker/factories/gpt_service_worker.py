import asyncio
import json
import logging
import typing as T  # noqa
from functools import wraps

from sqlalchemy.ext.asyncio import async_sessionmaker

from src.postgres.enums import CompetenceEnum
from src.rabbitmq.worker.factory import RabbitMQWorkerFactory
from src.repos.factories.temp_data import TempDataRepo
from src.repos.factories.user_question import TgUserQuestionRepo
from src.services.factories.answer_process import AnswerProcessService
from src.services.factories.result import ResultService
from src.services.factories.user_question import UserQuestionService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def async_log(func):
    @wraps(func)
    async def wrapper(self, uq_id):
        user_id = uq_id.get('uq_id', 'Unknown user_id')
        logger.info(f"uq_id: {user_id} >>> {func.__name__}")
        result = await func(self, uq_id)
        return result
    return wrapper


class GPTWorker(RabbitMQWorkerFactory):
    def __init__(
        self,
        session: async_sessionmaker,
        temp_data_repo: TempDataRepo,
        uq_repo: TgUserQuestionRepo,
        dsn_string: str,
        queue_name: str,
        heartbeat: int,
        result_service: ResultService,
        answer_process_service: AnswerProcessService,
    ):
        super().__init__(temp_data_repo, dsn_string, queue_name, heartbeat=heartbeat)
        self.temp_data_repo = temp_data_repo
        self.uq_repo = uq_repo
        self.session = session
        self.result_service = result_service
        self.answer_process_service = answer_process_service

    async def start_listening(self, routing_key, func):
        self.result_service.check_or_load_models()
        await super().start_listening(routing_key, func)

    @async_log
    async def process_result_local_model_task(self, data: T.Dict[str, T.Any]):
        instance, user, question = await self.uq_repo.get_uq_with_relations(uq_id=data['uq_id'])
        competence = question.competence
        extended_output = True if str(user.id) in self.result_service.settings.bot.admin_ids else False

        if competence == CompetenceEnum.writing:
            result = await self.result_service.generate_result(
                instance, competence, premium=data['priority'], extended_output=extended_output
            )

        elif competence == CompetenceEnum.speaking:
            result = await self.result_service.generate_result(
                instance, competence, premium=data['priority'], extended_output=extended_output)

        else:
            return

        if result:
            await UserQuestionService.update_uq(self.session, instance, json.dumps(result))
            await self.publish(
                {'user_id': user.id, 'result': result},
                'tg_bot_return_simple_result_to_user',
                self.get_priority(data['priority'])
            )
