import logging
import typing as T  # noqa

from sqlalchemy import select, and_, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.libs.adapter import Adapter
from src.postgres.models.tg_user import TgUser
from src.postgres.models.tg_user_pts import TgUserPts
from src.postgres.models.tg_user_question import TgUserQuestion
from src.postgres.models.tg_user_wallet import TgUserWallet
from src.repos.factories.activity import ActivityRepo
from src.repos.factories.user import TgUserRepo
from src.services.factory import ServiceFactory
from src.settings import Settings


class TgUserService(ServiceFactory):
    def __init__(
        self,
        repo: TgUserRepo,
        activity_repo: ActivityRepo,
        adapter: Adapter,
        session: async_sessionmaker,
        settings: Settings
    ) -> None:
        super().__init__(repo, adapter, session, settings)
        self.repo = repo
        self.activity_repo = activity_repo

    async def get_user_referrals(self, user_id: int, count_only: bool = True) -> T.Union[int, T.List[TgUser]]:
        async with self.session() as session:
            if count_only:
                query = select(func.count()).select_from(self.repo.model).where(self.repo.model.referrer_id == user_id)
                result = await session.execute(query)
                count = result.scalar_one()
                return count
            else:
                query = select(self.repo.model).where(self.repo.model.referrer_id == user_id)
                result = await session.execute(query)
                referrals = result.scalars().all()
                return referrals  # noqa

    async def get_tg_user_by_uq_id(self, uq_id: int) -> TgUser:
        async with self.session() as session:
            result = await session.execute(
                select(TgUser)
                .join(TgUserQuestion, TgUser.id == TgUserQuestion.user_id)
                .where(and_(TgUserQuestion.id == uq_id))
            )
            user = result.scalars().first()
            return user

    async def get_or_create_tg_user(
        self,
        user_id: int,
        username: T.Optional[str] = None,
        referrer_id: int = None,
        umt_data_dict: T.Optional[T.Dict] = None
    ) -> TgUser:
        user = await self.repo.get_tg_user_by_tg_id(user_id=user_id)
        if not user:
            user = await self.repo.create_tg_user(
                user_id=user_id, username=username, referrer_id=referrer_id, umt_data_dict=umt_data_dict
            )
            await self.mark_user_pts(user_id, 'start', 2)
            await self.mark_user_activity(user.id, 'add start free pt')
        return user

    async def mark_user_activity(self, user_id: int, activity_name: str) -> None:
        await self.activity_repo.create_user_activity(user_id, activity_name)

    async def mark_user_balance(self, user_id: int, channel: str, amount: int, currency: str) -> TgUserWallet:
        return await self.activity_repo.create_tg_user_wallet(user_id, channel, amount, currency)

    async def mark_user_pts(self, user_id: int, pts_channel: str, balance_movement: int) -> TgUserPts:
        return await self.activity_repo.create_tg_user_pts(user_id, pts_channel, balance_movement)

    async def add_points(self, user_id: int, points: int) -> T.Optional[TgUser]:
        async with self.session() as session:
            async with session.begin():
                try:
                    user_query = await session.execute(
                        select(TgUser)
                        .where(and_(TgUser.id == user_id)).with_for_update()
                    )
                    user = user_query.scalars().first()
                    if user is None:
                        return
                    user.pts += points
                    session.add(user)
                    await session.commit()
                    await session.refresh(user)
                    return user
                except SQLAlchemyError as e:
                    await session.rollback()
                    logging.critical(e)
                    return
