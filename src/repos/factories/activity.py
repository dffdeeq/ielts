import typing as T  # noqa

from sqlalchemy.ext.asyncio import async_sessionmaker

from src.postgres.models.tg_user_activity import TgUserActivity
from src.postgres.models.tg_user_pts import TgUserPts
from src.postgres.models.tg_user_wallet import TgUserWallet
from src.repos.factory import RepoFactory


class ActivityRepo(RepoFactory):
    def __init__(self, model: T.Type[TgUserActivity], session: async_sessionmaker):
        super().__init__(model, session)

    async def create_tg_user_pts(self, user_id: int, pts_channel: str, balance_movement: int) -> TgUserPts:
        instance = await self.insert_one(
            model=TgUserPts, user_id=user_id, pts_channel=pts_channel, balance_movement=balance_movement)
        if instance is not None:
            return instance

    async def create_tg_user_wallet(
        self,
        user_id: int,
        channel: str,
        amount: int,
        currency: str
    ) -> T.Optional[TgUserWallet]:
        instance = await self.insert_one(
            model=TgUserWallet, user_id=user_id, channel=channel, amount=amount, currency=currency)
        if instance is not None:
            return instance

    async def create_user_activity(self, user_id: int, activity_name: str) -> TgUserActivity:
        instance = await self.insert_one(user_id=user_id, activity_name=activity_name)
        return instance
