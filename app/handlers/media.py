import asyncio
import io
import logging

from aiogram import F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from app.keyboards import batch_add_kb, batch_edit_kb, meta_kb
from app.loader import bot, dp
from app.services import history
from app.services.metadata import apply_metadata, read_metadata
from app.states import EditMetadata, BatchProcess

logger = logging.getLogger(__name__)


# ─── Single file ───

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
        cover_log = f"cover={'YES' if cover else 'NONE'} size={len(cover[1]) if cover else 0}"
        logger.info("handle_audio: title=%s artist=%s %s", title, artist, cover_log)
        await state.update_data(buf=buf, title=title, artist=artist, cover=cover, file_name=file_name)
        await msg.answer(
            f"🎵 <b>{title}</b>\n👤 {artist}\n\nЧто изменить?",
            reply_markup=meta_kb
        )
    except Exception as e:
        logger.exception("Audio processing error")
        await msg.answer(f"❌ Ошибка: {e}")


# ─── Edit callbacks (single file) ───

@dp.callback_query(F.data == "edit_title")
async def edit_title_cb(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await cb.message.edit_text("Введи новое название:")
    await state.set_state(EditMetadata.waiting_for_title)


@dp.message(EditMetadata.waiting_for_title)
async def process_title(msg: Message, state: FSMContext):
    await state.update_data(title=msg.text)
    await state.set_state(None)
    await msg.answer(f"✅ Название: <b>{msg.text}</b>", reply_markup=meta_kb)


@dp.callback_query(F.data == "edit_artist")
async def edit_artist_cb(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await cb.message.edit_text("Введи нового исполнителя:")
    await state.set_state(EditMetadata.waiting_for_artist)


@dp.message(EditMetadata.waiting_for_artist)
async def process_artist(msg: Message, state: FSMContext):
    await state.update_data(artist=msg.text)
    await state.set_state(None)
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
        logger.info("process_cover: got file id=%s path=%s size=%s", file.file_id, file.file_path, file.file_size)
        if not file.file_path:
            raise ValueError("File path not found")
        buf = await bot.download_file(file.file_path)
        if not buf:
            raise ValueError("Failed to download photo")
        raw = buf.read()
        logger.info("process_cover: downloaded photo size=%d first_bytes=%s",
                     len(raw), raw[:50].hex() if raw else "EMPTY")
        logger.info("process_cover: storing cover=('image/jpeg', %d bytes)", len(raw))
        await state.update_data(cover=("image/jpeg", raw))
        await state.set_state(None)
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

    if cover:
        logger.info("send_audio: cover PRESENT mime=%s data_size=%d first_bytes=%s",
                     cover[0], len(cover[1]), cover[1][:50].hex() if cover[1] else "EMPTY")
    else:
        logger.info("send_audio: cover is None")

    await cb.message.edit_text("📝 Обновляю метаданные...")
    out = await asyncio.to_thread(apply_metadata, buf, title, artist, cover)

    await cb.message.edit_text("📤 Отправляю...")
    output_name = file_name.rsplit(".", 1)[0] + ".mp3"
    edited = out.read()

    kwargs = dict(
        title=title,
        performer=artist,
    )
    if cover:
        kwargs["thumbnail"] = BufferedInputFile(cover[1], filename="cover.jpg")
        logger.info("send_audio: adding thumbnail %d bytes", len(cover[1]))

    await cb.message.answer_audio(
        BufferedInputFile(edited, filename=output_name),
        **kwargs,
    )
    history.add(cb.from_user.id, title, artist, edited)
    await state.clear()


# ─── Batch: start (from "В очередь" button) ───

@dp.callback_query(F.data == "add_to_batch")
async def add_to_batch_cb(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    data = await state.get_data()
    buf = data["buf"]
    title = data.get("title", data.get("file_name", "audio.mp3"))
    file_name = data.get("file_name", "audio.mp3")

    raw = buf.read()
    files = [{"buf": io.BytesIO(raw), "title": title, "file_name": file_name}]

    await state.update_data(batch_files=files)
    await state.set_state(BatchProcess.collecting)
    await cb.message.edit_text(
        f"✅ Файл добавлен в очередь (всего 1)\nОтправь следующий MP3:",
        reply_markup=batch_add_kb
    )


# ─── Batch: collecting files ───

@dp.message((F.audio | F.document), BatchProcess.collecting)
async def handle_batch_file(msg: Message, state: FSMContext):
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
    try:
        file = await bot.get_file(file_id)
        if not file.file_path:
            raise ValueError("File path not found")
        buf = await bot.download_file(file.file_path)
        if not buf:
            raise ValueError("Failed to download file")

        raw = buf.read()
        data = await state.get_data()
        files = data.get("batch_files", [])
        files.append({"buf": io.BytesIO(raw), "title": file_name, "file_name": file_name})
        await state.update_data(batch_files=files)

        await msg.answer(
            f"✅ Файл #{len(files)} добавлен (всего {len(files)})",
            reply_markup=batch_add_kb
        )
    except Exception as e:
        logger.exception("Batch add error")
        await msg.answer(f"❌ Ошибка: {e}")


@dp.callback_query(F.data == "batch_add_more")
async def batch_add_more_cb(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await cb.message.edit_text("Отправь следующий MP3 файл:")


@dp.callback_query(F.data == "batch_done")
async def batch_done_cb(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    data = await state.get_data()
    files = data.get("batch_files", [])
    if not files:
        await cb.message.edit_text("❌ Нет файлов в очереди")
        await state.clear()
        return
    await state.update_data(batch_title="", batch_artist="")
    await cb.message.edit_text(
        f"📁 {len(files)} файлов\n\nТеперь укажи название и исполнителя для всех:",
        reply_markup=batch_edit_kb
    )


# ─── Batch: edit metadata ───

@dp.callback_query(F.data == "batch_edit_title")
async def batch_edit_title_cb(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await cb.message.edit_text("Введи название для всех файлов:")
    await state.set_state(BatchProcess.waiting_for_title)


@dp.message(BatchProcess.waiting_for_title)
async def batch_process_title(msg: Message, state: FSMContext):
    await state.update_data(batch_title=msg.text)
    data = await state.get_data()
    files = data.get("batch_files", [])
    title = data.get("batch_title", "")
    artist = data.get("batch_artist", "")
    await msg.answer(
        f"📁 {len(files)} файлов\nНазвание: <b>{title or '—'}</b>\nИсполнитель: <b>{artist or '—'}</b>",
        reply_markup=batch_edit_kb
    )


@dp.callback_query(F.data == "batch_edit_artist")
async def batch_edit_artist_cb(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await cb.message.edit_text("Введи исполнителя для всех файлов:")
    await state.set_state(BatchProcess.waiting_for_artist)


@dp.message(BatchProcess.waiting_for_artist)
async def batch_process_artist(msg: Message, state: FSMContext):
    await state.update_data(batch_artist=msg.text)
    data = await state.get_data()
    files = data.get("batch_files", [])
    title = data.get("batch_title", "")
    artist = data.get("batch_artist", "")
    await msg.answer(
        f"📁 {len(files)} файлов\nНазвание: <b>{title or '—'}</b>\nИсполнитель: <b>{artist or '—'}</b>",
        reply_markup=batch_edit_kb
    )


@dp.callback_query(F.data == "batch_send")
async def batch_send_cb(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    data = await state.get_data()
    files = data.get("batch_files", [])
    btitle = data.get("batch_title", "")
    bartist = data.get("batch_artist", "")

    if not files:
        await cb.message.edit_text("❌ Нет файлов")
        await state.clear()
        return
    if not btitle and not bartist:
        await cb.message.edit_text("❌ Укажи хотя бы название или исполнителя")
        return

    await cb.message.edit_text(f"⏳ Обрабатываю {len(files)} файлов...")

    for i, item in enumerate(files, 1):
        try:
            fbuf = item["buf"]
            fname = item.get("file_name", f"track_{i}.mp3")
            ftitle = btitle or item.get("title", fname)
            fartist = bartist or "Unknown"

            logger.info("batch_send item %d: title=%s artist=%s no_cover", i, ftitle, fartist)
            out = await asyncio.to_thread(apply_metadata, fbuf, ftitle, fartist)

            output_name = fname.rsplit(".", 1)[0] + ".mp3"
            edited = out.read()
            await cb.message.answer_audio(
                BufferedInputFile(edited, filename=output_name),
                title=ftitle,
                performer=fartist,
            )
            history.add(cb.from_user.id, ftitle, fartist, edited)
        except Exception as e:
            logger.exception("Batch item %d error", i)
            await cb.message.answer(f"❌ Ошибка в файле #{i}: {e}")

    await state.clear()
    await cb.message.delete()
