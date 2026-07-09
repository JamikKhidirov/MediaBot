from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.loader import bot, dp
from app.services import history


@dp.message(Command("start"))
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        "🎵 <b>AudioEditor</b>\n\n"
        "Пришли MP3 файл, и я помогу изменить название, исполнителя и обложку\n\n"
        "Команды:\n"
        "/history — последние 5 отредактированных песен\n"
        "/cancel — отменить"
    )


@dp.message(Command("cancel"))
async def cmd_cancel(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("❌ Отменено")


@dp.message(Command("history"))
async def cmd_history(msg: Message):
    entries = history.get_all(msg.from_user.id)
    if not entries:
        await msg.answer("📭 История пуста")
        return
    lines = []
    kb_btns = []
    for i, (title, artist, _) in enumerate(entries, 1):
        lines.append(f"{i}. {title} — {artist}")
        kb_btns.append([InlineKeyboardButton(text=f"{i}. {title}", callback_data=f"history_get_{i-1}")])
    kb = InlineKeyboardMarkup(inline_keyboard=kb_btns)
    await msg.answer("📜 <b>Последние отредактированные:</b>\n" + "\n".join(lines), reply_markup=kb)


@dp.callback_query(F.data.startswith("history_get_"))
async def history_get_cb(cb: CallbackQuery):
    await cb.answer()
    idx = int(cb.data.split("_")[2])
    entry = history.get(cb.from_user.id, idx)
    if not entry:
        await cb.message.edit_text("❌ Запись не найдена")
        return
    title, artist, data = entry
    await cb.message.answer_audio(
        BufferedInputFile(data, filename=f"{title}.mp3"),
        title=title,
        performer=artist,
    )
