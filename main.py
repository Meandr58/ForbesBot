import asyncio
import aiohttp
import logging
import transliterate
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN, API_URL, API_HOST, API_KEY

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

logging.basicConfig(level=logging.INFO)


# Функция для выполнения запросов к API Forbes
async def get_data(endpoint: str):
    headers = {
        "x-rapidapi-host": API_HOST,
        "x-rapidapi-key": API_KEY
    }
    await asyncio.sleep(1)  # Задержка на 1 секунду

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/{endpoint}", headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                logging.error(
                    f"Error fetching data from {endpoint}: {response.status}, response: {await response.text()}")
                return None


# Обработчик команды /start
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(f'Привет, {message.from_user.first_name}! Это бот Forbes Billionaires. Вызов доступных команд - /help')


@dp.message(Command("top_billionaires"))
async def top_billionaires(message: Message):
    data = await get_data("list.php")

    # Логируем полученные данные
    logging.info(f"Fetched data: {data}")

    # Проверяем, что данные получены и являются словарем
    if data:
        # Проверяем, что есть ключ 'ranking' и это список
        if 'ranking' in data and isinstance(data['ranking'], list):
            top_10 = data['ranking'][:10]  # Получаем топ-10 миллиардеров
            response_text = "Топ 10 миллиардеров мира:\n"
            for idx, billionaire in enumerate(top_10, 1):
                response_text += f"{idx}. {billionaire['name']} – ${billionaire['current_worth']}B ({billionaire['country']})\n"
            await message.answer(response_text)
        else:
            await message.answer("Не удалось получить данные о миллиардерах.")
    else:
        await message.answer("Не удалось получить данные о миллиардерах.")

# Обработчик команды /billionaire_info [имя] – информация о миллиардере по имени
@dp.message(Command("billionaire_info"))
async def billionaire_info(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Укажите имя миллиардера: /billionaire_info [имя]")
        return

    name = args[1].strip().lower()
    data = await get_data("list.php")  # Запрашиваем список миллиардеров
    if data and "ranking" in data:
        billionaires = data["ranking"]
        billionaire = next((b for b in billionaires if b['name'].lower() == name), None)
        if billionaire:
            response = (
                f"Имя: {billionaire['name']}\n"
                f"Состояние: ${billionaire['current_worth']}B\n"
                f"Страна: {billionaire['country']}\n"
                f"Источник дохода: {billionaire['source']}\n"
                f"Возраст: {billionaire['age']}\n"
                f"Ссылка на фото: {billionaire['image']}"
            )
            await message.answer(response)
        else:
            await message.answer(f"Миллиардер с именем {name} не найден.")
    else:
        await message.answer("Не удалось получить данные о миллиардерах.")

# Обработчик команды /richest_in_country [страна] – самый богатый человек в указанной стране
@dp.message(Command("richest_in_country"))
async def richest_in_country(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Укажите страну: /richest_in_country [страна]")
        return

    country = args[1].strip().lower()
    data = await get_data("list.php")  # Запрашиваем список миллиардеров
    if data and "ranking" in data:
        billionaires = data["ranking"]
        billionaires_from_country = [b for b in billionaires if b['country'].lower() == country]
        if billionaires_from_country:
            richest = max(billionaires_from_country, key=lambda b: b['current_worth'])
            response = (
                f"Самый богатый человек в {richest['country']}:\n"
                f"{richest['name']} – ${richest['current_worth']}B\n"
                f"Источник дохода: {richest['source']}\n"
                f"Возраст: {richest['age']}\n"
                f"Ссылка на фото: {richest['image']}"
            )
            await message.answer(response)
        else:
            await message.answer(f"В стране {country} не найдено миллиардеров.")
    else:
        await message.answer(f"Не удалось получить данные для страны {country}.")


# Обработчик команды /help
@dp.message(Command("help"))
async def process_help_command(message: Message):
    await message.answer("Этот бот выполняет команды:\n"
                         "/top_billionaires – Топ 10 миллиардеров\n"
                         "/billionaire_info [имя] – Информация о миллиардере\n"
                         "/richest_in_country [страна] – Самый богатый человек в стране\n"
                         "Страна и Имя - на английском. Имя - Имя и Фамилия")

# Основная функция для запуска бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
