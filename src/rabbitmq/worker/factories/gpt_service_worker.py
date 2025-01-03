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
from src.services.factories.status_service import StatusService
from src.services.factories.tg_user import TgUserService
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
        status_service: StatusService,
        user_service: TgUserService,
        uq_service: UserQuestionService
    ):
        super().__init__(temp_data_repo, dsn_string, queue_name, heartbeat=heartbeat)
        self.temp_data_repo = temp_data_repo
        self.uq_repo = uq_repo
        self.session = session
        self.result_service = result_service
        self.answer_process_service = answer_process_service
        self.status_service = status_service
        self.user_service = user_service
        self.uq_service = uq_service

    async def start_listening(self, routing_key, func):
        self.result_service.check_or_load_models()
        await super().start_listening(routing_key, func)

    @async_log
    async def process_result_local_model_task(self, data: T.Dict[str, T.Any]):
        await self.status_service.change_qa_status(data['uq_id'], 'Results generation in progress.')
        instance, user, question = await self.uq_repo.get_uq_with_relations(uq_id=data['uq_id'])
        competence = question.competence
        is_admin = True if str(user.id) in self.result_service.settings.bot.admin_ids else False

        if competence == CompetenceEnum.writing:
            result, extended_output, raw_results = await self.result_service.generate_result(
                instance, competence, premium=data['priority'], extended_output=True
            )
            bad_pronunciation = False

        elif competence == CompetenceEnum.speaking:
            result, extended_output, raw_results = await self.result_service.generate_result(
                instance, competence, premium=data['priority'], extended_output=True
            )
            await self.user_service.mark_user_activity(user.id, 'use voice request')

            bad_pronunciation = True if raw_results['pr_Pronunciation'] < 7 else False
        else:
            return

        less_than_three_points = True if user.pts < 3 else False

        if result:
            uq_result = result.copy()
            if extended_output:
                uq_result.insert(0, extended_output)
                if is_admin:
                    result.insert(0, extended_output)
            await self.uq_service.update_uq(instance, json.dumps(uq_result))
            await self.status_service.change_qa_status(data['uq_id'], 'Sending results for processing.')
            await self.user_service.mark_user_activity(user.id, f'response generated {competence.value}')
            await self.publish(
                {
                    'user_id': user.id,
                    'result': result,
                    'uq_id': data['uq_id'],
                    'less_than_three_points': less_than_three_points,
                    'bad_pronunciation': bad_pronunciation,
                },
                'tg_bot_return_simple_result_to_user',
                self.get_priority(data['priority'])
            )
