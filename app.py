import logging
import json
import os
from datetime import datetime
import asyncio  # Импортируем asyncio для запуска

from aiogram import Bot, Dispatcher, Router, types, F  # Обновленные импорты
from aiogram.filters import CommandStart, StateFilter # Добавляем фильтры
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage # Обновленный импорт FSM Storage
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton # Уточняем импорты типов

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
# ВАЖНО: Замените 'YOUR_TELEGRAM_BOT_TOKEN' на ваш реальный токен
API_TOKEN = '7793952602:AAFzTxminZRId6hCw07SfjZj5yNFG1AOGqg'
storage = MemoryStorage()
# Bot и Dispatcher создаются немного по-другому
# Dispatcher теперь основной объект, Bot передается при запуске
dp = Dispatcher(storage=storage)
# Используем Router для организации хэндлеров
router = Router()
dp.include_router(router) # Подключаем роутер к диспетчеру

# Файлы для хранения данных
USERS_FILE = 'users.json'
BANKS_FILE = 'banks.json'


# Загрузка данных (без изменений)
def load_data(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {filename}")
            return {}
    return {}


def save_data(data, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving data to {filename}: {e}")


# Загружаем данные при старте
users = load_data(USERS_FILE)
banks = load_data(BANKS_FILE)


# Состояния FSM (определение без изменений, импорт State, StatesGroup обновлен)
class BankStates(StatesGroup):
    waiting_for_bank_name = State()
    waiting_for_amount = State()
    waiting_for_withdraw_amount = State()
    waiting_for_new_user = State()
    waiting_for_bank_selection_deposit = State() # Отдельное состояние для выбора банка при пополнении
    waiting_for_bank_selection_withdraw = State() # Отдельное состояние для выбора банка при снятии
    waiting_for_bank_selection_reset = State() # Отдельное состояние для выбора банка при обнулении
    waiting_for_bank_selection_view = State() # Отдельное состояние для выбора банка для просмотра


# Проверка прав доступа (без изменений)
def is_authorized(user_id):
    return str(user_id) in users


# Проверка прав доступа к банку (без изменений)
def has_bank_access(user_id, bank_name):
    user_id = str(user_id)
    if bank_name not in banks:
        return False
    # Проверяем создателя или список допущенных пользователей
    # Добавляем проверку на существование ключа allowed_users
    return (user_id == str(banks[bank_name].get('created_by')) or
            user_id in banks[bank_name].get('allowed_users', []))


# --- Клавиатуры ---
# Используем builder для большей гибкости, хотя старый способ тоже работает
# Этот код оставлен в старом стиле для простоты, но builder рекомендуется для v3
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Создать новый банк")],
            [KeyboardButton(text="Список банков")],
            [KeyboardButton(text="Мой баланс")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_bank_operations_keyboard(bank_name):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Добавить деньги")],
            [KeyboardButton(text="Снять деньги")],
            [KeyboardButton(text="Обнулить банк")],
            [KeyboardButton(text=f"Добавить пользователя в {bank_name}")],
            [KeyboardButton(text="Назад")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_banks_list_keyboard(user_id):
    # Показываем только те банки, к которым у пользователя есть доступ
    accessible_banks = [name for name in banks if has_bank_access(user_id, name)]
    buttons = [[KeyboardButton(text=bank_name)] for bank_name in accessible_banks]
    buttons.append([KeyboardButton(text="Назад")])
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard


# --- Обработчики команд и сообщений ---
# Используем декораторы @router.* вместо @dp.*
# Используем фильтры aiogram 3 (CommandStart, F.text)

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext): # state можно убрать, если не используется
    user_id = str(message.from_user.id)

    if not is_authorized(user_id):
        users[user_id] = {
            "name": message.from_user.full_name,
            "username": message.from_user.username or "N/A", # Добавим username
            "join_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_data(users, USERS_FILE)
        await message.answer("Добро пожаловать! Вы были добавлены в систему.")
    else:
         # Обновим имя и username, если изменились
        users[user_id]["name"] = message.from_user.full_name
        users[user_id]["username"] = message.from_user.username or "N/A"
        save_data(users, USERS_FILE)

    await message.answer("Выберите действие:", reply_markup=get_main_keyboard())
    await state.clear() # Сбрасываем состояние на всякий случай


@router.message(F.text == "Назад")
async def cmd_back(message: Message, state: FSMContext):
    # При нажатии "Назад" всегда сбрасываем состояние
    await state.clear()
    await message.answer("Главное меню:", reply_markup=get_main_keyboard())


@router.message(F.text == "Создать новый банк")
async def cmd_create_bank_prompt(message: Message, state: FSMContext):
    if not is_authorized(message.from_user.id):
        await message.answer("У вас нет доступа к этой функции.")
        return

    await state.set_state(BankStates.waiting_for_bank_name)
    await message.answer("Введите название нового банка:", reply_markup=types.ReplyKeyboardRemove()) # Убираем клавиатуру


@router.message(BankStates.waiting_for_bank_name) # Фильтр по состоянию
async def process_bank_name(message: Message, state: FSMContext):
    bank_name = message.text.strip()

    if not bank_name:
        await message.answer("Название банка не может быть пустым. Попробуйте снова.")
        return

    if bank_name in banks:
        await message.answer("Банк с таким именем уже существует. Выберите другое название.")
        return

    # Проверка на запрещенные имена (например, команды)
    if bank_name in ["Назад", "Создать новый банк", "Список банков", "Мой баланс", "Добавить деньги", "Снять деньги", "Обнулить банк"] or bank_name.startswith("Добавить пользователя в "):
         await message.answer("Это название зарезервировано. Выберите другое.")
         return

    banks[bank_name] = {
        "balance": 0,
        "created_by": message.from_user.id,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "history": [],
        "allowed_users": [str(message.from_user.id)] # Создатель автоматически добавляется
    }

    save_data(banks, BANKS_FILE)
    await state.clear() # Используем clear() вместо finish()
    await message.answer(f"Банк '{bank_name}' успешно создан!", reply_markup=get_main_keyboard())


@router.message(F.text == "Список банков")
async def cmd_banks_list(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    if not is_authorized(user_id):
        await message.answer("У вас нет доступа к этой функции.")
        return

    accessible_banks = [name for name in banks if has_bank_access(user_id, name)]

    if not accessible_banks:
        await message.answer("У вас нет доступных банков.")
        return

    await state.set_state(BankStates.waiting_for_bank_selection_view) # Устанавливаем состояние ожидания выбора банка
    await message.answer("Выберите банк:", reply_markup=get_banks_list_keyboard(user_id))


# Обработчик для выбора банка из списка для просмотра
@router.message(BankStates.waiting_for_bank_selection_view, F.text) # Ловим любой текст в этом состоянии
async def process_bank_selection_view(message: Message, state: FSMContext):
    bank_name = message.text
    user_id = str(message.from_user.id)

    # Дополнительная проверка, что выбранный банк действительно есть и доступен
    if bank_name == "Назад": # Обработка кнопки Назад
        await state.clear()
        await message.answer("Главное меню:", reply_markup=get_main_keyboard())
        return

    if bank_name not in banks or not has_bank_access(user_id, bank_name):
        await message.answer("Банк не найден или у вас нет доступа. Выберите из списка:",
                             reply_markup=get_banks_list_keyboard(user_id))
        return # Остаемся в том же состоянии

    bank = banks[bank_name]
    creator_id = str(bank.get('created_by', 'Неизвестно'))
    creator_name = users.get(creator_id, {}).get('name', 'Неизвестно')
    allowed_users_count = len(bank.get('allowed_users', []))

    response = (
        f"Банк: {bank_name}\n"
        f"Баланс: {bank['balance']}\n"
        f"Создан: {bank.get('created_at', 'Неизвестно')}\n"
        f"Создатель: {creator_name} (ID: {creator_id})\n"
        f"Пользователи с доступом: {allowed_users_count}"
    )

    await state.clear() # Выходим из состояния выбора
    # Сохраняем выбранный банк в данных состояния для дальнейших операций
    await state.update_data(current_bank=bank_name)
    await message.answer(response, reply_markup=get_bank_operations_keyboard(bank_name))


# --- Операции с выбранным банком ---

# Функция для получения текущего выбранного банка из состояния
async def get_current_bank(state: FSMContext, message: Message) -> str | None:
    data = await state.get_data()
    bank_name = data.get("current_bank")
    if not bank_name:
        await message.answer("Сначала выберите банк из списка.", reply_markup=get_main_keyboard())
        await state.clear()
        return None
    if bank_name not in banks:
        await message.answer(f"Банк '{bank_name}' больше не существует. Выберите другой.", reply_markup=get_main_keyboard())
        await state.clear()
        return None
    if not has_bank_access(message.from_user.id, bank_name):
        await message.answer(f"У вас больше нет доступа к банку '{bank_name}'.", reply_markup=get_main_keyboard())
        await state.clear()
        return None
    return bank_name


@router.message(F.text.startswith("Добавить пользователя в "))
async def cmd_add_user_to_bank_prompt(message: Message, state: FSMContext):
    bank_name = await get_current_bank(state, message)
    if not bank_name:
        return # Ошибка уже отправлена в get_current_bank

    # Проверка прав: только создатель может добавлять пользователей
    if str(message.from_user.id) != str(banks[bank_name].get('created_by')):
         await message.answer("Только создатель банка может добавлять пользователей.")
         return

    # Не нужно извлекать имя банка из текста кнопки, оно уже в state
    # bank_name = message.text.replace("Добавить пользователя в ", "").strip() # Это больше не нужно

    await state.set_state(BankStates.waiting_for_new_user)
    # Имя банка уже есть в state.update_data({'current_bank': bank_name})
    await message.answer(f"Введите ID пользователя Telegram (число), которого хотите добавить в банк '{bank_name}':",
                         reply_markup=types.ReplyKeyboardRemove())


@router.message(BankStates.waiting_for_new_user)
async def process_new_user(message: Message, state: FSMContext):
    bank_name = await get_current_bank(state, message)
    if not bank_name:
        await state.clear() # Сброс состояния, если банк не найден
        return

    new_user_id_str = message.text.strip()

    # Проверка, что введен ID (число)
    if not new_user_id_str.isdigit():
        await message.answer("Пожалуйста, введите корректный числовой ID пользователя.")
        # Не выходим из состояния, даем попробовать еще раз
        return

    new_user_id = str(new_user_id_str) # Работаем со строками для ID

    # Проверяем, известен ли боту этот пользователь вообще
    if new_user_id not in users:
        await message.answer(f"Пользователь с ID {new_user_id} ни разу не запускал этого бота. "
                             f"Попросите его запустить команду /start у бота.")
        # Оставляем пользователя в состоянии, чтобы он мог ввести другой ID или отменить
        return

    # Проверка, что пользователь не пытается добавить самого себя (хотя он и так создатель)
    if new_user_id == str(banks[bank_name].get('created_by')):
        await message.answer("Создатель банка уже имеет полный доступ.")
        await state.set_state(None) # Выходим из ожидания ID, но оставляем выбранный банк
        await message.answer(f"Операции для банка '{bank_name}':", reply_markup=get_bank_operations_keyboard(bank_name))
        return

    # Инициализируем список, если его нет (хотя он должен быть с версии выше)
    if 'allowed_users' not in banks[bank_name]:
        banks[bank_name]['allowed_users'] = [str(banks[bank_name].get('created_by'))]

    if new_user_id not in banks[bank_name]['allowed_users']:
        banks[bank_name]['allowed_users'].append(new_user_id)
        save_data(banks, BANKS_FILE)
        new_user_name = users.get(new_user_id, {}).get('name', f'ID: {new_user_id}')
        await message.answer(
            f"Пользователь {new_user_name} добавлен в банк '{bank_name}' с полными правами.")
    else:
        await message.answer("Этот пользователь уже имеет доступ к данному банку.")

    # await state.clear() # Не очищаем полностью, только состояние ввода ID
    await state.set_state(None) # Убираем конкретное состояние ожидания ID
    # Возвращаем клавиатуру операций с текущим банком
    await message.answer(f"Операции для банка '{bank_name}':", reply_markup=get_bank_operations_keyboard(bank_name))


@router.message(F.text == "Добавить деньги")
async def cmd_add_money_prompt(message: Message, state: FSMContext):
    bank_name = await get_current_bank(state, message)
    if not bank_name:
        return

    await state.set_state(BankStates.waiting_for_amount)
    await message.answer("Введите сумму для добавления:", reply_markup=types.ReplyKeyboardRemove())


@router.message(BankStates.waiting_for_amount)
async def process_add_money(message: Message, state: FSMContext):
    bank_name = await get_current_bank(state, message)
    if not bank_name:
        await state.clear()
        return

    try:
        # Заменяем запятые на точки для корректного float
        amount_str = message.text.replace(',', '.').strip()
        amount = float(amount_str)

        if amount <= 0:
            await message.answer("Сумма должна быть положительной.")
            # Не выходим из состояния
            return
        if amount > 1_000_000_000: # Ограничение на всякий случай
             await message.answer("Слишком большая сумма.")
             return

        # Форматируем сумму для вывода
        formatted_amount = "{:,.2f}".format(amount).replace(',', ' ').replace('.', ',')

        banks[bank_name]['balance'] += amount
        # Добавляем запись в историю
        banks[bank_name].setdefault('history', []).append({
            "type": "deposit",
            "amount": amount,
            "user_id": message.from_user.id,
            "user_name": users.get(str(message.from_user.id), {}).get('name', 'Unknown'),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        save_data(banks, BANKS_FILE)
        new_balance_formatted = "{:,.2f}".format(banks[bank_name]['balance']).replace(',', ' ').replace('.', ',')
        await message.answer(f"Добавлено {formatted_amount} в банк '{bank_name}'.\nНовый баланс: {new_balance_formatted}",
                             reply_markup=get_bank_operations_keyboard(bank_name))
        # await state.clear() # Не очищаем полностью, только состояние ввода суммы
        await state.set_state(None) # Сбрасываем состояние ожидания суммы

    except ValueError:
        await message.answer("Пожалуйста, введите корректную числовую сумму (например, 100 или 50.5).")
        # Не выходим из состояния


@router.message(F.text == "Снять деньги")
async def cmd_withdraw_money_prompt(message: Message, state: FSMContext):
    bank_name = await get_current_bank(state, message)
    if not bank_name:
        return

    await state.set_state(BankStates.waiting_for_withdraw_amount)
    await message.answer("Введите сумму для снятия:", reply_markup=types.ReplyKeyboardRemove())


@router.message(BankStates.waiting_for_withdraw_amount)
async def process_withdraw_money(message: Message, state: FSMContext):
    bank_name = await get_current_bank(state, message)
    if not bank_name:
        await state.clear()
        return

    try:
        amount_str = message.text.replace(',', '.').strip()
        amount = float(amount_str)

        if amount <= 0:
            await message.answer("Сумма должна быть положительной.")
            return

        current_balance = banks[bank_name].get('balance', 0)
        if current_balance < amount:
            await message.answer(f"Недостаточно средств в банке '{bank_name}'.\n"
                                 f"Доступно: {'{:,.2f}'.format(current_balance).replace(',', ' ').replace('.', ',')}")
            # await state.clear() # Выходим из состояния, так как операция невозможна
            await state.set_state(None)
            await message.answer(f"Операции для банка '{bank_name}':", reply_markup=get_bank_operations_keyboard(bank_name))
            return

        formatted_amount = "{:,.2f}".format(amount).replace(',', ' ').replace('.', ',')

        banks[bank_name]['balance'] -= amount
        banks[bank_name].setdefault('history', []).append({
            "type": "withdraw",
            "amount": amount,
            "user_id": message.from_user.id,
            "user_name": users.get(str(message.from_user.id), {}).get('name', 'Unknown'),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        save_data(banks, BANKS_FILE)
        new_balance_formatted = "{:,.2f}".format(banks[bank_name]['balance']).replace(',', ' ').replace('.', ',')
        await message.answer(f"Снято {formatted_amount} из банка '{bank_name}'.\nНовый баланс: {new_balance_formatted}",
                             reply_markup=get_bank_operations_keyboard(bank_name))
        # await state.clear()
        await state.set_state(None)

    except ValueError:
        await message.answer("Пожалуйста, введите корректную числовую сумму.")


@router.message(F.text == "Обнулить банк")
async def cmd_reset_bank(message: Message, state: FSMContext):
    bank_name = await get_current_bank(state, message)
    if not bank_name:
        return

    # Добавим проверку прав: только создатель может обнулить банк
    if str(message.from_user.id) != str(banks[bank_name].get('created_by')):
        await message.answer("Только создатель банка может его обнулить.")
        return

    banks[bank_name]['balance'] = 0
    banks[bank_name].setdefault('history', []).append({
        "type": "reset",
        "amount": 0, # Указываем сумму 0 для сброса
        "user_id": message.from_user.id,
        "user_name": users.get(str(message.from_user.id), {}).get('name', 'Unknown'),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    save_data(banks, BANKS_FILE)
    await message.answer(f"Банк '{bank_name}' обнулен. Баланс: 0",
                         reply_markup=get_bank_operations_keyboard(bank_name))
    # Состояние не менялось, очищать не нужно, но на всякий случай:
    await state.set_state(None)


@router.message(F.text == "Мой баланс")
async def cmd_balance(message: Message, state: FSMContext): # Добавил state для возможного сброса
    user_id = str(message.from_user.id)
    if not is_authorized(user_id):
        await message.answer("Вы не зарегистрированы. Начните с /start")
        return

    accessible_banks_info = []
    for bank_name, bank_data in banks.items():
        if has_bank_access(user_id, bank_name):
            balance_formatted = "{:,.2f}".format(bank_data.get('balance', 0)).replace(',', ' ').replace('.', ',')
            accessible_banks_info.append(f"'{bank_name}': {balance_formatted}")

    if accessible_banks_info:
        response = "Баланс ваших доступных банков:\n" + "\n".join(accessible_banks_info)
    else:
        response = "У вас пока нет доступных банков."

    await message.answer(response, reply_markup=get_main_keyboard()) # Возвращаем главную клавиатуру
    await state.clear() # Сбрасываем состояние, если было какое-то


# --- Запуск бота ---
async def main():
    # Создаем объект бота здесь
    bot = Bot(token=API_TOKEN)
    # Запускаем polling
    # skip_updates можно использовать для пропуска старых апдейтов при перезапуске
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())