
# Легальная альтернатива: простая капча для новых пользователей внутри вашего бота.
# Никаких обходов чужих капч нет.
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram import types, Dispatcher

class CaptchaStates(StatesGroup):
    WAITING = State()

CAPTCHA_QUESTION = "Подтверди, что ты человек: выбери правильный ответ 2+2=?"
CAPTCHA_ANSWERS = ["3", "4", "5"]

def register_captcha(dp: Dispatcher):
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for a in CAPTCHA_ANSWERS:
        kb.add(KeyboardButton(a))

    @dp.message_handler(commands=['start'], state='*')
    async def start(message: types.Message, state: FSMContext):
        await CaptchaStates.WAITING.set()
        await message.answer(CAPTCHA_QUESTION, reply_markup=kb)

    @dp.message_handler(state=CaptchaStates.WAITING)
    async def check(message: types.Message, state: FSMContext):
        if message.text == "4":
            await message.answer("Спасибо! Доступ открыт ✅", reply_markup=types.ReplyKeyboardRemove())
            await state.finish()
        else:
            await message.answer("Неверно. Попробуй ещё раз.")
