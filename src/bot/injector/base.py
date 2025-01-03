from src.libs.adapter import Adapter
from src.libs.factories.mp3tts import MP3TTSClient
from src.libs.http_client import HttpClient
from src.postgres.factory import initialize_postgres_pool
from src.postgres.models.poll_feedback import PollFeedback
from src.postgres.models.question import Question
from src.postgres.models.subscription import Subscription
from src.postgres.models.temp_data import TempData
from src.postgres.models.tg_user import TgUser
from src.postgres.models.tg_user_activity import TgUserActivity
from src.postgres.models.tg_user_question import TgUserQuestion
from src.postgres.models.metrics_data import MetricsData
from src.rabbitmq.producer.factories.mp3tts import MP3TTSProducer
from src.rabbitmq.producer.factories.gpt import GPTProducer
from src.repos.factories.activity import ActivityRepo
from src.repos.factories.feedback import FeedbackRepo
from src.repos.factories.question import QuestionRepo
from src.repos.factories.subscription import SubscriptionRepo
from src.repos.factories.temp_data import TempDataRepo
from src.repos.factories.user import TgUserRepo
from src.repos.factories.user_question import TgUserQuestionRepo
from src.repos.factories.metrics_data import MetricsDataRepo
from src.services.factories.answer_process import AnswerProcessService
from src.services.factories.feedback import FeedbackService
from src.services.factories.question import QuestionService
from src.services.factories.status_service import StatusService
from src.services.factories.subscription import SubscriptionService
from src.services.factories.tg_user import TgUserService
from src.services.factories.user_question import UserQuestionService
from src.services.factories.voice import VoiceService
from src.services.factories.metrics import MetricsService
from src.services.factories.S3 import S3Service
from src.settings import Settings


class BaseInjector:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.session = initialize_postgres_pool(settings.postgres)
        self.http_client = HttpClient()
        self.adapter = Adapter(self.settings)
        self.mp3tts_client = MP3TTSClient(http_client=self.http_client, settings=self.settings.mp3tts)
        tg_user_repo = TgUserRepo(TgUser, self.session)
        tg_user_question_repo = TgUserQuestionRepo(TgUserQuestion, self.session)
        activity_repo = ActivityRepo(TgUserActivity, self.session)
        subscription_repo = SubscriptionRepo(Subscription, self.session)

        self.subscription_service = SubscriptionService(
            repo=subscription_repo,
            adapter=self.adapter,
            session=self.session,
            settings=self.settings
        )
        self.s3 = S3Service(
            repo=TempDataRepo(
                TempData,
                self.session
            ),
            adapter=Adapter(
                settings=self.settings,
            ),
            session=self.session,
            settings=self.settings
        )
        self.question_service = QuestionService(
            s3_service=self.s3,
            repo=QuestionRepo(Question, self.session),
            adapter=self.adapter,
            session=self.session,
            settings=self.settings
        )
        self.uq_service = UserQuestionService(
            repo=tg_user_question_repo,
            adapter=self.adapter,
            session=self.session,
            settings=self.settings,
            user_repo=tg_user_repo,
            activity_repo=activity_repo
        )
        self.tg_user_service = TgUserService(
            repo=tg_user_repo,
            activity_repo=activity_repo,
            adapter=self.adapter,
            session=self.session,
            settings=self.settings,
        )
        self.apihost_producer = MP3TTSProducer(
            dsn_string=settings.rabbitmq.dsn,
            exchange_name='direct',
            adapter=self.adapter
        )
        self.gpt_producer = GPTProducer(
            dsn_string=settings.rabbitmq.dsn,
            exchange_name='direct',
            adapter=self.adapter
        )
        self.answer_process = AnswerProcessService(
            repo=TempDataRepo(TempData, self.session),
            adapter=self.adapter,
            session=self.session,
            settings=self.settings,
            user_qa_repo=tg_user_question_repo
        )
        self.status_service = StatusService(
            user_qa_repo=tg_user_question_repo,
            adapter=self.adapter,
            session=self.session,
            settings=self.settings,
        )
        self.feedback_service = FeedbackService(
            FeedbackRepo(
                PollFeedback,
                self.session
            ),
            self.adapter,
            self.session,
            self.settings
        )
        self.metrics_service = MetricsService(
            repo=MetricsDataRepo(
                MetricsData,
                self.session
            ),
            adapter=self.adapter,
            session=self.session,
            settings=self.settings,
        )
        self.voice_service = VoiceService(
            s3_service=self.s3,
            repo=QuestionRepo(Question, self.session),
            adapter=self.adapter,
            session=self.session,
            settings=self.settings
        )
