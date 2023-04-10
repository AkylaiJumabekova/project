"""Сервер Telegram бота, запускаемый непосредственно"""
import logging
from aiogram import Bot, Dispatcher, executor, types
import exceptions
import expenses
from categories import Categories
from envparse import Env

"""Включаем логирование, чтобы не пропустить важные сообщения"""
logging.basicConfig(level=logging.INFO)

"""Связываемся с переменными виртуального окружения"""
env = Env()
TOKEN = env.str("TOKEN")
USER_ID = env.int("USER_ID")

"""Объект бота"""
bot = Bot(token=TOKEN)

"""Диспетчер"""
dp = Dispatcher(bot)


def authentication_check(func):
    """Аутентификация — пропуск сообщений только от одного Telegram аккаунта"""
    async def wrapper(message):
        if message["from"]["id"] != USER_ID:
            return await message.reply("Извините, это закрытый бот", reply=False)
        return await func(message)
    return wrapper


@dp.message_handler(commands=["start", "help"])
@authentication_check
async def send_welcome(message: types.Message):
    """Отправляет приветственное сообщение и помощь по боту"""
    await message.answer(
        "Бот для учёта финансов\n\n"
        "Чтобы добавить расход введите: сумма категория\n"
        "Чтобы вывести сегодняшнюю статистику: /today\n"
        "Чтобы вывести статистику за текущий месяц: /month\n"
        "Увидеть последние внесённые расходы: /expenses\n"
        "Узнать, какие есть категории трат: /categories")


@dp.message_handler(lambda message: message.text.startswith("/del"))
@authentication_check
async def del_expense(message: types.Message):
    """Удаляет одну запись о расходе по её идентификатору"""
    row_id = int(message.text[4:])
    expenses.delete_expense(row_id)
    answer_message = "Запись о расходе удалена"
    await message.answer(answer_message)


@dp.message_handler(commands=["categories"])
@authentication_check
async def categories_list(message: types.Message):
    """Отправляет список категорий расходов"""
    categories = Categories().get_all_categories()
    answer_message = "Категории трат:\n\n* " +\
            ("\n* ".join([c.name+' ('+", ".join(c.aliases)+')' for c in categories]))
    await message.answer(answer_message)


@dp.message_handler(commands=["today"])
@authentication_check
async def today_statistics(message: types.Message):
    """Отправляет статистику трат за сегодня"""
    answer_message = expenses.get_today_statistics()
    await message.answer(answer_message)


@dp.message_handler(commands=["month"])
@authentication_check
async def month_statistics(message: types.Message):
    """Отправляет статистику трат текущего месяца"""
    answer_message = expenses.get_month_statistics()
    await message.answer(answer_message)


@dp.message_handler(commands=["expenses"])
@authentication_check
async def list_expenses(message: types.Message):
    """Отправляет последние несколько записей о расходах"""
    last_expenses = expenses.last()
    if not last_expenses:
        await message.answer("Расходы ещё не заведены")
        return

    last_expenses_rows = [
        f"{expense.amount} руб. на {expense.category_name} — нажми "
        f"/del{expense.id} для удаления"
        for expense in last_expenses]
    answer_message = "Последние сохранённые траты:\n\n* " + "\n\n* "\
            .join(last_expenses_rows)
    await message.answer(answer_message)


@dp.message_handler()
async def add_expense(message: types.Message):
    """Добавляет новый расход"""
    try:
        expense = expenses.add_expense(message.text)
    except exceptions.NotCorrectMessage as e:
        await message.answer(str(e))
        return
    answer_message = (
        f"Добавлены траты {expense.amount} руб на {expense.category_name}.\n\n"
        f"{expenses.get_today_statistics()}")
    await message.answer(answer_message)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

