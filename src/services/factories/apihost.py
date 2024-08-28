import asyncio
import logging
import typing as T  # noqa
import uuid

from sqlalchemy.ext.asyncio import async_sessionmaker

from src.libs.adapter import Adapter
from src.repos.factories.user import TgUserRepo
from src.services.factory import ServiceFactory
from src.settings import Settings


class ApiHostService(ServiceFactory):
    def __init__(
        self,
        repo: TgUserRepo,
        adapter: Adapter,
        session: async_sessionmaker,
        settings: Settings,
    ) -> None:
        super().__init__(repo, adapter, session, settings)
        self.repo = repo

    async def send_to_transcription(self, filepaths: T.List[str]):
        transcribe_id = await self._send_files_to_transcription(filepaths)
        if transcribe_id:
            await asyncio.sleep(2)
            transcribe_id = await self._confirm_transcription(transcribe_id)
            return transcribe_id

    async def _send_files_to_transcription(self, filepaths: T.List[str]) -> uuid.UUID:
        try:
            transcription = await self.adapter.apihost_client.send_files_to_transcription(filepaths)
            return transcription.upload_id
        except Exception as e:
            logging.error(e)

    async def _confirm_transcription(self, transcription_id: uuid.UUID) -> uuid.UUID:
        try:
            transcription = await self.adapter.apihost_client.confirm_transcription(transcription_id)
            return transcription.transcribe_id
        except Exception as e:
            logging.error(e)