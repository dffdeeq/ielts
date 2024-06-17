import typing as T # noqa

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.postgres.models.tg_user_question import TgUserQuestion
from src.repos.factory import RepoFactory


class TgUserQuestionRepo(RepoFactory):
    def __init__(self, model: T.Type[TgUserQuestion], session: async_sessionmaker):
        super().__init__(model, session)

    async def get_or_create_user_question(self, user_id: int, question_id: int) -> T.Optional[TgUserQuestion]:
        instance = await self.get_user_question(user_id, question_id)
        if not instance:
            instance = await self.create_user_question(user_id, question_id)
        return instance

    async def update_user_question(
        self,
        uq_id: int,
        answer_json: T.Optional[dict] = None,
        result_json: T.Optional[dict] = None,
        status: bool = False
    ):
        await self.update(
            conditions={'id': uq_id},
            values={'user_answer_json': answer_json, 'user_result_json': result_json, 'status': status})

    async def get_user_question(self, user_id, question_id) -> T.Optional[TgUserQuestion]:
        async with self.session() as session:
            instance = await session.execute(select(self.model).where(and_(
                self.model.user_id == user_id, self.model.question_id == question_id
            )))
        return instance.scalar_one_or_none()

    async def create_user_question(self, user_id, question_id) -> T.Optional[TgUserQuestion]:
        return await self.insert_one(user_id=user_id, question_id=question_id)
