import os

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.core.states import DevState
from src.bot.injector import INJECTOR
from src.rabbitmq.producer.factories.mp3tts import MP3TTSProducer
from src.rabbitmq.producer.factories.gpt import GPTProducer
from src.services.factories.S3 import S3Service
from src.services.factories.answer_process import AnswerProcessService

router = Router(name=__name__)


@router.callback_query(F.data.startswith('dev_run_task_processing'), INJECTOR.inject_tg_user)
async def dev_run_task_processing(callback: types.CallbackQuery, state: FSMContext):
    processing_option = callback.data.split()[1]
    prem = False
    if processing_option == 'premium':
        prem = True
    await state.set_state(DevState.get_uq_id)
    await state.set_data({'premium': prem})

    builder = InlineKeyboardBuilder([
        [
            InlineKeyboardButton(text='To mp3tts', callback_data='dev_to apihost'),
            InlineKeyboardButton(text='To gpt', callback_data='dev_to gpt'),
        ],
    ])

    await callback.message.edit_text(text='Choose', reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith('dev_to'), INJECTOR.inject_tg_user)
async def dev_to_(callback: types.CallbackQuery, state: FSMContext):
    to = callback.data.split()[1]
    await state.update_data({'to': to})
    await callback.message.edit_text(text='Enter uq_id')


@router.message(
    DevState.get_uq_id,
    INJECTOR.inject_s3,
    INJECTOR.inject_gpt_producer,
    INJECTOR.inject_answer_process,
    INJECTOR.inject_apihost_producer,
)
async def dev_run_task(
    message: types.Message,
    state: FSMContext,
    gpt_producer: GPTProducer,
    answer_process: AnswerProcessService,
    apihost_producer: MP3TTSProducer,
    s3: S3Service,
):
    try:
        uq_id = int(message.text)
    except ValueError:
        await message.answer(text='uq_id must be an integer')
        return

    state_data = await state.get_data()
    premium_queue = state_data['premium']
    to = state_data['to']

    if to == 'apihost':
        filepaths = await answer_process.get_temp_data_filepaths(answer_process.session, uq_id)
        if filepaths:
            s3.download_files_list([os.path.basename(key) for key in filepaths])
            await apihost_producer.create_task_send_to_transcription(filepaths, uq_id, premium_queue=premium_queue)
    elif to == 'gpt':
        await gpt_producer.create_task_generate_result(uq_id, premium_queue=premium_queue)
    else:
        await message.answer(text='"to" parameter is not supported')
        await state.clear()
        return

    await state.clear()
    await message.answer(text='Successful')
