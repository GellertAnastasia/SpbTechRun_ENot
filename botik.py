import logging
import sqlite3
import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove
from aiogram.utils import executor
from gigachatik import get_chat_completion, get_token, auth

# Настройки логирования
logging.basicConfig(level=logging.INFO)

# Настройка подключения к базе данных
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

# Создание таблиц, если их нет
cursor.execute('''
CREATE TABLE IF NOT EXISTS last_q (
    user_id INTEGER PRIMARY KEY,
    last_question TEXT
);
''')
conn.commit()

# Настройка бота
API_TOKEN = "7387894880:AAHMLSH2zisWzKgvhmKrKBc2ZLr3zxLA3WE"
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

# Клавиатуры
sogl_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

# Состояния
class Form(StatesGroup):
    waiting_for_id = State()

# Обработчик команды /start
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_id = message.from_user.id
    result = cursor.execute(f"SELECT * FROM last_q WHERE user_id={user_id}").fetchone()
    if not result:
        cursor.execute(f"INSERT INTO last_q (user_id) VALUES (?)", (user_id,))
        conn.commit()
    await bot.send_message(
        message.from_user.id,
        "Привет! Я помогу Вам автоматизировать процесс выдачи ипотеки с помощью моделей машинного обучения. \nВведите /id.",
    )

# Обработчик команды /id
@dp.message_handler(commands=['id'], state="*")
async def request_id(message: types.Message):
    await Form.waiting_for_id.set()
    await bot.send_message(message.from_user.id, "Пожалуйста, введите Ваш ID:")

@dp.message_handler(state=Form.waiting_for_id)
async def process_id(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    async with state.proxy() as data:
        data['user_id'] = int(message.text.strip())
    df = pd.read_csv('data.csv')  # Чтение CSV файла
    if data['user_id'] < len(df):

        row = df.iloc[data['user_id']]  # Получаем строку по индексу
        cursor.execute(f"UPDATE last_q SET idup=? WHERE user_id=?", (message.text.strip(), user_id))
        conn.commit()
        await bot.send_message(message.from_user.id, f"Ваша информация: \n{row.to_string()}")
    else:
        await bot.send_message(message.from_user.id, "К сожалению, мы не нашли информацию по указанному индексу.")
    await state.finish()


@dp.message_handler()
async def handle_messages(message: types.Message):
    user_id = message.from_user.id
    question = message.text

    # Получение токена
    try:
        token = get_token(auth)["access_token"]
    except Exception as e:
        logging.error(f"Ошибка при получении токена: {e}")
        await bot.send_message(user_id, "Произошла ошибка при обработке запроса. Попробуйте снова позже.")
        return

    # Отправка вопроса в GigaChat
    try:
        answer = get_chat_completion(token, f"ответь на вопрос про ипотеку и кредит: {question}\n если вопрос не  про ипотеку, отклоняй вопросы").json()['choices'][0]['message']['content']
    except Exception as e:
        logging.error(f"Ошибка при обращении к GigaChat: {e}")
        await bot.send_message(user_id, "Произошла ошибка при обработке запроса. Попробуйте снова позже.")
        return

    # Сохранение последнего вопроса в базу данных
    try:
        cursor.execute(f"SELECT * FROM last_q WHERE user_id=?", (user_id,))
        result = cursor.fetchone()
        if result is None:
            cursor.execute(f"INSERT INTO last_q (user_id, question) VALUES (?, ?)", (user_id, question))
        else:
            cursor.execute(f"UPDATE last_q SET question=? WHERE user_id=?", (question, user_id))
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Ошибка при работе с базой данных: {e}")
        await bot.send_message(user_id, "Произошла ошибка при сохранении вопроса. Попробуйте снова позже.")
        return

    # Отправка ответа пользователю
    await bot.send_message(user_id, answer)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)