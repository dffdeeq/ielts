import json
import logging

from aiogram import Router, F, types
from aiogram.types import LabeledPrice

from src.bot.handlers.defaults.pricing_default import answer_pricing
from src.bot.injector import INJECTOR
from src.services.factories.tg_user import TgUserService

router = Router(name=__name__)


@router.callback_query(F.data == 'pricing', INJECTOR.inject_tg_user)
async def pricing_callback(callback: types.CallbackQuery, tg_user_service: TgUserService):
    await callback.answer()

    user = await tg_user_service.get_or_create_tg_user(callback.from_user.id)
    await answer_pricing(callback, user)


@router.callback_query(F.data.startswith('buy_pts_by_tg_stars'), INJECTOR.inject_tg_user)
async def buy_pts_by_tg_start(callback: types.CallbackQuery):
    await callback.answer()

    price = {
        3: [LabeledPrice(label="3 PTs", amount=150)],
        10: [LabeledPrice(label="10 PTs", amount=450)],
        100: [LabeledPrice(label="100 PTs", amount=4000)]
    }

    try:
        amount = int(callback.data.split()[1])
    except ValueError:
        logging.error('Cannot parse amount %s', callback.data.split()[1])
        return

    await callback.bot.send_invoice(
        chat_id=callback.from_user.id,
        title='IELTS Exam Bot: Your Personal Assistant for IELTS Preparation',
        description='Effective IELTS preparation with personalized exercises, expert tips, and a motivation system.',
        payload=json.dumps({
            'user_id': callback.from_user.id,
            'amount': amount
        }),
        currency='XTR',
        prices=price[amount]
    )


@router.pre_checkout_query()
async def precheckout_callback(pre_checkout_query: types.PreCheckoutQuery):
    logging.info(pre_checkout_query)
    if pre_checkout_query.total_amount:
        await pre_checkout_query.bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@router.message(F.successful_payment, INJECTOR.inject_tg_user)
async def successful_payment_handler(message: types.Message, tg_user_service: TgUserService):
    successful_payment = message.successful_payment
    logging.info(successful_payment)
    if not successful_payment:
        return

    invoice_payload = json.loads(successful_payment.invoice_payload)
    user_id_from_payload = invoice_payload['user_id']
    purchased_pts = invoice_payload['amount']

    if user_id_from_payload == message.from_user.id:
        await tg_user_service.add_points(user_id_from_payload, purchased_pts)
    else:
        logging.critical(f'Payment failed for user {message.from_user.id} (from payload - {user_id_from_payload}) '
                         f'(user_id_from_payload != message.from_user.id)')

    await message.answer("Thank you for your purchase! Your payment was successful.")
