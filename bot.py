import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, executor
from app import db, config

logging.basicConfig(level=logging.INFO)

bot = Bot(config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

RATE_MS = config.DEFAULT_DELAY_MS
CYCLE_SECONDS = config.DEFAULT_CYCLE_SECONDS

# --- Декоратор для команд без лишних аргументов ---
def safe_handler(handler):
    async def wrapper(message: types.Message, *args, **kwargs):
        return await handler(message)
    return wrapper

# --- Хендлеры ---
@dp.message_handler(commands=["start"])
@safe_handler
async def cmd_start(message: types.Message):
    await db.add_user(config.DB_PATH, message.from_user.id, message.from_user.first_name, message.from_user.username)
    await message.answer("Привет! Ты подписан на рассылки.")

@dp.message_handler(commands=["help"])
@safe_handler
async def cmd_help(message: types.Message):
    await message.answer("""Команды:
/stats — статистика
/broadcast — мастер рассылки
/schedule YYYY-MM-DD HH:MM — разовая рассылка
/schedule_every <seconds> — периодическая рассылка
/jobs — список задач
/cancel <job_id> — отмена задачи
/set_rate <ms> — задержка между сообщениями
/set_cycle <seconds> — интервал для периодических
/set_token <TOKEN> — сохранить новый токен (нужен рестарт)
""")

@dp.message_handler(commands=["stats"])
@safe_handler
async def cmd_stats(message: types.Message):
    count = await db.users_count(config.DB_PATH)
    await message.answer(f"Всего подписчиков: {count}")

@dp.message_handler(commands=["jobs"])
@safe_handler
async def cmd_jobs(message: types.Message):
    jobs = await db.list_jobs(config.DB_PATH)
    if not jobs:
        await message.answer("Список задач пуст.")
    else:
        text = "\n".join([f"ID {j[0]} | {j[1]} | {j[5]}" for j in jobs])
        await message.answer(f"Задачи:\n{text}")

@dp.message_handler(commands=["cancel"])
@safe_handler
async def cmd_cancel(message: types.Message):
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Использование: /cancel <job_id>")
        return
    await db.cancel_job(config.DB_PATH, int(parts[1]))
    await message.answer(f"Задача {parts[1]} отменена.")

@dp.message_handler(commands=["set_rate"])
@safe_handler
async def cmd_set_rate(message: types.Message):
    global RATE_MS
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Использование: /set_rate <ms>")
        return
    RATE_MS = int(parts[1])
    await message.answer(f"Задержка между сообщениями установлена: {RATE_MS} мс")

@dp.message_handler(commands=["set_cycle"])
@safe_handler
async def cmd_set_cycle(message: types.Message):
    global CYCLE_SECONDS
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Использование: /set_cycle <seconds>")
        return
    CYCLE_SECONDS = int(parts[1])
    await message.answer(f"Интервал периодических рассылок: {CYCLE_SECONDS} секунд")

@dp.message_handler(commands=["set_token"])
@safe_handler
async def cmd_set_token(message: types.Message):
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Использование: /set_token <TOKEN>")
        return
    token = parts[1]
    await message.answer(f"Новый токен сохранён, перезапустите бота: {token}")

# --- Отправка сообщений ---
async def send_message_with_media(user_id, text, media_file_id=None, parse_mode=None):
    try:
        if media_file_id:
            try:
                await bot.send_photo(user_id, photo=media_file_id, caption=text, parse_mode=parse_mode)
            except Exception:
                await bot.send_document(user_id, document=media_file_id, caption=text, parse_mode=parse_mode)
        else:
            await bot.send_message(user_id, text, parse_mode=parse_mode)
    except Exception as e:
        logging.warning(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

# --- Цикл рассылки ---
async def broadcast_loop():
    while True:
        try:
            jobs_list = await db.active_jobs(config.DB_PATH)
            users = await db.get_all_users(config.DB_PATH)
            for job in jobs_list:
                job_id, job_type, text, scheduled_at, interval_seconds, media_file_id, parse_mode = job

                # Разовая задача
                if job_type == "once":
                    if scheduled_at and datetime.utcnow().isoformat() >= scheduled_at:
                        for user_id in users:
                            await send_message_with_media(user_id, text, media_file_id, parse_mode)
                            await asyncio.sleep(RATE_MS / 1000)
                        await db.cancel_job(config.DB_PATH, job_id)

                # Периодическая задача
                elif job_type == "interval":
                    for user_id in users:
                        await send_message_with_media(user_id, text, media_file_id, parse_mode)
                        await asyncio.sleep(RATE_MS / 1000)

            await asyncio.sleep(5)
        except Exception as e:
            logging.error(f"Ошибка в цикле рассылки: {e}")
            await asyncio.sleep(5)

# --- Запуск бота ---
async def on_startup(dp):
    await db.init_db(config.DB_PATH)
    logging.info("Bot started")
    asyncio.create_task(broadcast_loop())

def main():
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

if __name__ == "__main__":
    main()
