from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.loader import dp


@dp.message(Command("start"))
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        "🎵 <b>AudioEditor</b>\n\n"
        "Пришли MP3 файл, и я помогу изменить название и исполнителя"
    )


@dp.message(Command("cancel"))
async def cmd_cancel(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("❌ Отменено")
