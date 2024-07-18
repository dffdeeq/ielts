from aiogram import Dispatcher

from .command_handler.menu_command import router as menu_command
from .command_handler.start_command import router as start_command
from .command_handler.admin_command import router as admin_command

from .message_handler.speaking import router as speaking_router
from .message_handler.menu import router as menu_router
from .message_handler.writing import router as writing_router
from .message_handler.pricing import router as pricing_router
from .message_handler.balance import router as balance_router
from .message_handler.admin import router as admin_router


def register_handlers(dp: Dispatcher):
    dp.include_router(menu_command)
    dp.include_router(start_command)
    dp.include_router(admin_command)

    dp.include_router(speaking_router)
    dp.include_router(menu_router)
    dp.include_router(writing_router)
    dp.include_router(pricing_router)
    dp.include_router(balance_router)
    dp.include_router(admin_router)
