import asyncio
from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
from aiogram.types import LabeledPrice

from config.messages import *
from services.keyboards import *
from config.settings import PAYMENTS_PROVIDER_TOKEN, BOT_TOKEN
from aiogram.enums import ParseMode
from database.database_mysql import UserDatabaseMySQL
from config.settings import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

db = UserDatabaseMySQL(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)

client_router = Router()
vpn_service = VPNService()

bot = Bot(token=BOT_TOKEN,
          default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2))

FREE_DAYS_SECONDS = 3 * 24 * 60 * 60


@client_router.message(CommandStart(deep_link=False))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    user = db.get_user(user_id)
    now = int(time.time())
    expiry_time = now + FREE_DAYS_SECONDS
    username = message.from_user.username or f"user{user_id}"

    if not user:
        vpn_data = await vpn_service.create_vpn_user(user_id, username)

        if vpn_data is not None:
            if 'uuid' in vpn_data and 'config' in vpn_data:
                db.add_user(user_id, username, vpn_data['uuid'], vpn_data['config'], expiry_time)
                caption = start_message(username)
                await message.answer_photo(photo=FSInputFile("logo.jpg"),
                                             caption=caption,
                                             parse_mode=ParseMode.MARKDOWN_V2,
                                             reply_markup=main_menu_kb)
            else:
                print("Ошибка: В vpn_data отсутствует ключ uuid или config")
        else:
            print("Ошибка: vpn_service.create_vpn_user вернул None")
    else:
        if user.get('expiry_time', 0) > now:
            await message.answer(success_message(username, user.get('expiry_time', 0)), reply_markup=main_menu_kb)
        else:
            await message.answer("👋 Ваша подписка закончилась. Оформите новую:",
                                 reply_markup=subscribe_kb)


@client_router.message(CommandStart(deep_link=True))
async def cmd_start(message: Message, command: CommandStart):
    user_id = message.from_user.id
    args = command.args  # строка после /start (параметры)
    referrer_id = None

    # Разбор параметра реферала (если есть)
    if args and args.startswith("ref_") and args[4:].isdigit():
        referrer_id = int(args[4:])

    user = db.get_user(user_id)
    username = message.from_user.username or f"user_{user_id}"
    now = int(time.time())
    expiry_time = now + FREE_DAYS_SECONDS
    if not user:
        # Первый запуск - создаем пользователя с 3 днями бесплатной подписки
        vpn_data = await vpn_service.create_vpn_user(user_id, username)
        if vpn_data is not None:
            # убедитесь, что поля vpn_uuid и vpn_config у vpn_data непустые
            if 'vpn_uuid' in vpn_data and 'vpn_config' in vpn_data:
                result = db.add_user(user_id, username, vpn_data['vpn_uuid'], vpn_data['vpn_config'], expiry_time)
                print('user insert result:', result)
                caption = start_message(username)
                await message.answer_photo(photo=FSInputFile("logo.jpg"),
                                             caption=caption,
                                             parse_mode=ParseMode.MARKDOWN_V2,
                                             reply_markup=main_menu_kb)
            else:
                print("Ошибка: В vpn_data отсутствует vpn_uuid или vpn_config")
        else:
            print("Ошибка: vpn_service.create_vpn_user вернул None")

        # Если есть реферал — продляем срок пригласившему
        if referrer_id and referrer_id != user_id:
            inviter = db.get_user(referrer_id)
            if inviter:
                old_expiry = inviter.get("expiry_time", 0)
                base_time = old_expiry if old_expiry > now else now
                new_expiry = base_time + 3 * 24 * 3600 * 1000  # +3 дня
                db.update_expiry(referrer_id, new_expiry)
                await bot.send_message(referrer_id,
                                       f"Ваш друг @{message.from_user.username or user_id} присоединился!"
                                       f" Подписка продлена ещё на 3 дня.")
    else:
        print(f"time left: {time.ctime(expiry_time)}")
        if user.get('expiry_time', 0) > now:
            await message.answer(f"👋 Ваша подписка активна до: {time.ctime(int(user.get('expiry_time')))}",
                                 reply_markup=main_menu_kb)
        else:
            await message.answer("👋 Ваша подписка закончилась. Оформите новую:",
                                 reply_markup=subscribe_kb)

@client_router.callback_query(F.data == "back_to_subs")
@client_router.callback_query(lambda c: c.data == "subscribe")
async def process_subscribe(call: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        await bot.delete_message(data['chat_id'], data['message1_id'])
        await bot.delete_message(data['chat_id'], data['message_id'])
        await state.clear()
    except:
        pass

    await call.message.delete()
    await call.message.answer("Выберите тариф подписки:", reply_markup=subscribe_kb)

@client_router.callback_query(F.data == "back_to_device")
@client_router.callback_query(F.data=="select_dev")
async def select_dev(call: CallbackQuery):
    await call.message.delete()
    await call.message.answer(choose_device(),
                              parse_mode=ParseMode.MARKDOWN_V2,
                              reply_markup=select_device_kb)


@client_router.callback_query(lambda c: c.data == "invite")
async def process_invite(call: CallbackQuery):
    user_id= call.from_user.id

    # Генерируем уникальную реферальную ссылку
    referral_link = f"https://t.me/{(await bot.me()).username}?start=ref_{user_id}"

    await call.message.delete()
    await call.message.answer(ref_link(referral_link),
                              parse_mode=ParseMode.MARKDOWN_V2,
                              reply_markup=back_to_menu_kb)


@client_router.callback_query(lambda c: c.data == "help")
async def process_help(call: CallbackQuery):
    await call.message.delete()
    await call.message.answer(help_message(),
                              parse_mode=ParseMode.MARKDOWN_V2,
                              reply_markup=back_to_menu_kb)


@client_router.callback_query(lambda c: c.data == "back_to_menu")
async def process_back(call: CallbackQuery):
    username = call.from_user.username
    user_id = call.from_user.id

    user = db.get_user(user_id)
    expiry_time = user.get("expiry_time", 0)

    await call.message.delete()
    await call.message.answer(success_message(username, expiry_time),
                              parse_mode=ParseMode.MARKDOWN_V2,
                              reply_markup=main_menu_kb)


@client_router.callback_query(lambda c: c.data.startswith("plan_"))
async def process_plan(call: CallbackQuery, state: FSMContext):
    months = int(call.data.split("_")[1])
    await call.message.delete()  # Удаляет инлайн-клавиатуру
    # Здесь дальше вызываем оплату (send_invoice) или другую логику
    mes1 = await call.message.answer(f"Вы выбрали подписку на {months} месяцев. Оформление платежа...")
    await state.update_data(message1_id=mes1.message_id)
    await asyncio.sleep(3)
    #await call.message.delete()
    if months == 1:
        amount = 9900  # amount в копейках (99 рублей)
        description = "Доступ на месяц"
    elif months == 3:
        amount = 24900
        description = 'Доступ на 3 месяца'
    elif months == 6:
        amount = 44900 # 75%
        description = 'Доступ на полгода'
    elif months == 12:
        amount = 79900 # 66%
        description = 'Доступ на год'

    prices = [LabeledPrice(label="Подписка на VPN", amount=amount)]
    invoice = await call.message.answer_invoice(
        title="VPN Подписка",
        description=description,
        provider_token=PAYMENTS_PROVIDER_TOKEN,
        currency="RUB",
        prices=prices,
        start_parameter="vpn-subscription",
        payload="vpn-payment-payload"
    )
    await state.update_data(chat_id =invoice.chat.id, message_id = invoice.message_id)
    await call.message.answer('Если хотите изменить выбор подписки, то нажмите кнопку ниже',
                              reply_markup=back_to_subs_kb)


@client_router.pre_checkout_query(lambda query: True)
async def checkout(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@client_router.message(F.successful_payment)
async def successful_payment(message: Message, state: FSMContext):
    await message.answer("Оплата прошла успешно!\nСпасибо за покупку.")
    user_id, months = map(int, message.successful_payment.invoice_payload.split(":"))
    now = int(time.time())
    user = db.get_user(user_id)

    current_expiry = user.get("expiry_time", 0) if user else 0
    base_time = current_expiry if current_expiry > now else now

    # Добавляем месяцы (30 дней на месяц в секундах)
    new_expiry = base_time + months * 30 * 24 * 3600 * 1000

    # Обновляем в базе
    db.update_expiry(user_id, new_expiry)
    await message.answer(success_pay(new_expiry),
                         reply_markup=select_device_kb)


@client_router.callback_query(F.data.startswith("select_device_"))
async def select_device(call: CallbackQuery):
    device = call.data.split("_")[2]
    user_id = call.from_user.id

    if device == "1":
        await call.message.edit_text('Для подключения вашего IPhone следуйте инструкциям',
                                     reply_markup=await device1_kb(user_id))
    elif device == "2":
        await call.message.edit_text('Для подключения вашего телефона следуйте инструкциям',
                                     reply_markup=await device2_kb(user_id))
    elif device == "3":
        await call.message.edit_text('Для подключения вашего ПК следуйте инструкциям',
                                     reply_markup=await device3_kb(user_id))
    elif device == "4":
        await call.message.edit_text('Для подключения вашего Mac следуйте инструкциям',
                                     reply_markup=await device1_kb(user_id))