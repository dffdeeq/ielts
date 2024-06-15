from src.libs.adapter import Adapter
from src.libs.factories.apihost import ApiHostClient
from src.libs.http_client import HttpClient
from src.postgres.factory import initialize_postgres_pool
from src.postgres.models.question import Question
from src.postgres.models.tg_user import TgUser
from src.rabbitmq.producer.factories.apihost import ApiHostProducer
from src.repos.factories.question import QuestionRepo
from src.repos.factories.user import TgUserRepo
from src.services.factories.gpt import GPTService
from src.services.factories.tg_bot import TgBotService
from src.services.factories.voice import VoiceService
from src.settings import Settings


class BaseInjector:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.session = initialize_postgres_pool(settings.postgres)
        self.http_client = HttpClient()
        self.adapter = Adapter(self.settings)
        self.apihost_client = ApiHostClient(http_client=self.http_client, settings=self.settings.apihost)
        self.gpt_service = GPTService(
            repo=QuestionRepo(Question, self.session),
            adapter=self.adapter,
            session=self.session,
            settings=self.settings
        )
        self.tg_bot_service = TgBotService(
            repo=TgUserRepo(TgUser, self.session),
            adapter=self.adapter,
            session=self.session,
            settings=self.settings
        )
        self.voice_service = VoiceService(
            repo=QuestionRepo(Question, self.session),
            adapter=self.adapter,
            session=self.session,
            settings=self.settings
        )
        self.apihost_producer = ApiHostProducer(
            dsn_string=settings.rabbitmq.dsn,
            exchange_name='',
            routing_key='',
            adapter=self.adapter
        )
