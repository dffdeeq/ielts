import asyncio
import logging

from src.libs.adapter import Adapter
from src.neural_network import ScoreGeneratorNNModel
from src.postgres.factory import initialize_postgres_pool
from src.postgres.models.question import Question
from src.postgres.models.temp_data import TempData
from src.postgres.models.tg_user_question import TgUserQuestion
from src.rabbitmq.worker.factories.gpt_service_worker import GPTWorker
from src.repos.factories.question import QuestionRepo
from src.repos.factories.temp_data import TempDataRepo
from src.repos.factories.user_question import TgUserQuestionRepo
from src.services.factories.answer_process import AnswerProcessService
from src.services.factories.result import ResultService
from src.settings import Settings

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger('aio_pika').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
logging.getLogger('torch').setLevel(logging.WARNING)
logging.getLogger('pyannote').setLevel(logging.WARNING)
logging.getLogger('pytorch_lightning').setLevel(logging.WARNING)


async def main():
    settings = Settings.new()
    session = initialize_postgres_pool(settings.postgres)
    adapter = Adapter(settings)
    repo = TempDataRepo(TempData, session)
    uq_repo = TgUserQuestionRepo(TgUserQuestion, session)
    result_service = ResultService(
        repo=QuestionRepo(Question, session),
        adapter=adapter,
        session=session,
        settings=settings,
        nn_service=ScoreGeneratorNNModel(settings.nn_models)
    )
    answer_process_service = AnswerProcessService(
        repo=repo,
        adapter=adapter,
        session=session,
        settings=settings,
        user_qa_repo=uq_repo
    )
    gpt_worker = GPTWorker(
        temp_data_repo=repo,
        uq_repo=uq_repo,
        session=session,
        result_service=result_service,
        dsn_string=settings.rabbitmq.dsn,
        queue_name='gpt',
        heartbeat=600,
        answer_process_service=answer_process_service,
    )
    await gpt_worker.start_listening(
        'gpt_generate_result_use_local_model', gpt_worker.process_result_local_model_task)


if __name__ == '__main__':
    asyncio.run(main())
