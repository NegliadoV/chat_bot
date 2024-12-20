import nest_asyncio
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from quiz_data import quiz_data
from database import create_table, update_quiz_index, get_quiz_index, update_score, get_score
from dotenv import load_dotenv
import os

# Применение nest_asyncio для работы в асинхронной среде
nest_asyncio.apply()

#Токен
load_dotenv()
API_TOKEN = os.getenv('API_TOKEN')

# логирование
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

async def get_question(message, user_id):
    """Отправляем вопрос пользователю."""
    current_question_index = await get_quiz_index(user_id)
    if current_question_index >= len(quiz_data):
        score = await get_score(user_id)
        await message.answer(f"Квиз завершен! Ваш результат: {score} из {len(quiz_data)}.")
        return

    question_data = quiz_data[current_question_index]
    options_text = '\n'.join(f"{i+1}. {option}" for i, option in enumerate(question_data['options']))
    await message.answer(f"{question_data['question']}\n{options_text}")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я квиз бот. Введите /quiz, чтобы начать.")

@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    user_id = message.from_user.id
    await update_quiz_index(user_id, 0)
    await update_score(user_id, 0)  # Обнуляем счет перед началом
    await get_question(message, user_id)

@dp.message(lambda message: message.text.isdigit())
async def handle_answer(message: types.Message):
    user_id = message.from_user.id
    current_question_index = await get_quiz_index(user_id)

    if current_question_index >= len(quiz_data):
        return  # Квиз завершен

    question_data = quiz_data[current_question_index]
    answer = int(message.text) - 1  # Ответ пользователя

    if 0 <= answer < len(question_data['options']):
        if answer == question_data['correct_option']:
            score = await get_score(user_id)
            score += 1
            await update_score(user_id, score)
            await message.answer(f"Правильный ответ! Ваш текущий результат: {score} из {len(quiz_data)}.")
        else:
            correct_answer_text = question_data['options'][question_data['correct_option']]
            await message.answer(f"Неправильно. Правильный ответ: {correct_answer_text}")
    else:
        await message.answer("Пожалуйста, выберите правильный номер ответа (например, 1, 2, 3 или 4).")

    await update_quiz_index(user_id, current_question_index + 1)
    await get_question(message, user_id)

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    user_id = message.from_user.id
    score = await get_score(user_id)
    await message.answer(f"Ваш результат: {score} из {len(quiz_data)}.")

async def main():
    await create_table()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
