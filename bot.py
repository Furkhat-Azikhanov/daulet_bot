import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)
from openai import OpenAI
from dotenv import load_dotenv
import asyncio
import time

# Создаем .env файл и загружаем переменные окружения
def create_env_file():
    env_content = '''TELEGRAM_TOKEN=7844872007:AAFcTUHB6bk1NDnNw-XTnl4TpGxuWAsREYc
OPENAI_API_KEY=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'''
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)

# Создаем файл .env и загружаем переменные
create_env_file()
load_dotenv()

# Проверяем наличие переменных окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise ValueError("Не удалось загрузить токены из .env файла")

# Инициализация
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
client = OpenAI(api_key=OPENAI_API_KEY)
ASSISTANT_ID = "asst_mlm40BuRGpCTWjoi15UfGFMp"

# Тексты приветствий
WELCOME_TEXT_RU = """Привет! Меня зовут Aidar. Я профориентатор и карьерный консультант с 10-летним опытом.

Я помогу вам выбрать профессию, узнать о будущих трендах и разобраться, какие навыки нужны для работы в транспорте, ЖД и логистике.

Как я могу помочь?

Задавайте вопросы на казахском или русском — отвечу кратко и по делу!"""

WELCOME_TEXT_KZ = """Сәлем! Менің атым – Айдар.
Мен 10 жылдық тәжірибесі бар кәсіби бағдар маманы және карьералық кеңесшімін.

Сізге мамандық таңдауға, болашақтағы трендтерді түсінуге және көлік, теміржол мен логистика салаларында қандай дағдылар қажет екенін анықтауға көмектесемін.

Сізге қалай көмектесе аламын?

Сұрақтарыңызды қазақ немесе орыс тілінде қойыңыз – қысқа әрі нақты жауап беремін!"""

# Создание клавиатур
def get_language_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇷🇺 Русский"), KeyboardButton(text="🇰🇿 Қазақша")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

def get_main_menu_keyboard(lang='ru'):
    if lang == 'ru':
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Пройти тест", url="http://89.35.124.179/")],
            [InlineKeyboardButton(text="💬 Консультация", callback_data="consultation")]
        ])
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Тест тапсыру", url="http://89.35.124.179/")],
            [InlineKeyboardButton(text="💬 Кеңес алу", callback_data="consultation")]
        ])
    return keyboard

# Обработчики сообщений
@dp.message(CommandStart())
async def send_welcome(message: Message):
    await message.reply(
        "Выберите язык / Тілді таңдаңыз:",
        reply_markup=get_language_keyboard()
    )

@dp.message(lambda message: message.text in ["🇷🇺 Русский", "🇰🇿 Қазақша"])
async def handle_language_choice(message: Message):
    lang = 'ru' if message.text == "🇷🇺 Русский" else 'kz'
    welcome_text = WELCOME_TEXT_RU if lang == 'ru' else WELCOME_TEXT_KZ
    await message.reply(
        welcome_text,
        reply_markup=get_main_menu_keyboard(lang)
    )

@dp.callback_query(lambda c: c.data == "consultation")
async def process_consultation(callback_query: types.CallbackQuery):
    await callback_query.answer()
    lang = 'ru'  # По умолчанию русский, можно добавить определение языка
    if lang == 'ru':
        await callback_query.message.reply("Пожалуйста, опишите ваш вопрос:")
    else:
        await callback_query.message.reply("Сұрағыңызды сипаттаңыз:")

async def get_assistant_response(message_text: str) -> str:
    try:
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message_text
        )

        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )

        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_status.status == 'completed':
                break
            elif run_status.status == 'failed':
                return "Извините, произошла ошибка при обработке запроса."
            time.sleep(1)

        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        return messages.data[0].content[0].text.value

    except Exception as e:
        return f"Ошибка при получении ответа: {str(e)}"

@dp.message()
async def process_message(message: Message):
    if not message.text:
        return
        
    try:
        processing_msg = await message.reply("Обрабатываю ваш запрос...")
        response = await get_assistant_response(message.text)
        await processing_msg.delete()
        await message.reply(response)

    except Exception as e:
        await message.reply(f"Произошла ошибка: {str(e)}")

async def main():
    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())