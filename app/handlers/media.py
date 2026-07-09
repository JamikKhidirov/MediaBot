import asyncio
import logging

from aiogram import F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from app.keyboards import meta_kb
from app.loader import bot, dp
from app.services.metadata import apply_metadata, read_metadata
from app.states import EditMetadata

logger = logging.getLogger(__name__)


@dp.message((F.audio | F.document), StateFilter(None))
async def handle_audio(msg: Message, state: FSMContext):
    file_id = None
    file_name = "audio.mp3"

    if msg.audio:
        file_id = msg.audio.file_id
        file_name = f"{msg.audio.title or 'audio'}.mp3"
    elif msg.document:
        if not msg.document.file_name or not msg.document.file_name.lower().endswith(".mp3"):
            await msg.answer("❌ Отправь MP3 файл")
            return
        file_id = msg.document.file_id
        file_name = msg.document.file_name

    if not file_id:
        return

    await msg.answer("⏳ Читаю метаданные...")

    try:
        file = await bot.get_file(file_id)
        if not file.file_path:
            raise ValueError("File path not found")

        buf = await bot.download_file(file.file_path)
        if not buf:
            raise ValueError("Failed to download file")

        title, artist, cover = await asyncio.to_thread(read_metadata, buf)

        await state.update_data(buf=buf, title=title, artist=artist, cover=cover, file_name=file_name)
        await msg.answer(
            f"🎵 <b>{title}</b>\n👤 {artist}\n\nЧто изменить?",
            reply_markup=meta_kb
        )
    except Exception as e:
        logger.exception("Audio processing error")
        await msg.answer(f"❌ Ошибка: {e}")


@dp.callback_query(F.data == "edit_title")
async def edit_title_cb(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await cb.message.edit_text("Введи новое название:")
    await state.set_state(EditMetadata.waiting_for_title)


@dp.message(EditMetadata.waiting_for_title)
async def process_title(msg: Message, state: FSMContext):
    await state.update_data(title=msg.text)
    await msg.answer(f"✅ Название: <b>{msg.text}</b>", reply_markup=meta_kb)


@dp.callback_query(F.data == "edit_artist")
async def edit_artist_cb(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await cb.message.edit_text("Введи нового исполнителя:")
    await state.set_state(EditMetadata.waiting_for_artist)


@dp.message(EditMetadata.waiting_for_artist)
async def process_artist(msg: Message, state: FSMContext):
    await state.update_data(artist=msg.text)
    await msg.answer(f"✅ Исполнитель: <b>{msg.text}</b>", reply_markup=meta_kb)


@dp.callback_query(F.data == "edit_cover")
async def edit_cover_cb(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await cb.message.edit_text("Отправь фото для обложки:")
    await state.set_state(EditMetadata.waiting_for_cover)


@dp.message(F.photo, EditMetadata.waiting_for_cover)
async def process_cover(msg: Message, state: FSMContext):
    try:
        file = await bot.get_file(msg.photo[-1].file_id)
        if not file.file_path:
            raise ValueError("File path not found")

        buf = await bot.download_file(file.file_path)
        if not buf:
            raise ValueError("Failed to download photo")

        await state.update_data(cover=("image/jpeg", buf.read()))
        await msg.answer("✅ Обложка обновлена!", reply_markup=meta_kb)
    except Exception as e:
        logger.exception("Cover process error")
        await msg.answer(f"❌ Ошибка: {e}")


@dp.callback_query(F.data == "send_audio")
async def send_audio_cb(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    data = await state.get_data()
    buf = data["buf"]
    title = data.get("title", "Unknown")
    artist = data.get("artist", "Unknown")
    cover = data.get("cover")
    file_name = data.get("file_name", "audio.mp3")

    await cb.message.edit_text("📝 Обновляю метаданные...")
    await asyncio.to_thread(apply_metadata, buf, title, artist, cover)

    await cb.message.edit_text("📤 Отправляю...")
    output_name = file_name.rsplit(".", 1)[0] + ".mp3"
    await cb.message.answer_audio(
        BufferedInputFile(buf.read(), filename=output_name),
        title=title,
        performer=artist,
    )
    await state.clear()
