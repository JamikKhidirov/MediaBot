from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

meta_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✏️ Название", callback_data="edit_title"),
     InlineKeyboardButton(text="✏️ Исполнитель", callback_data="edit_artist")],
    [InlineKeyboardButton(text="🖼 Обложка", callback_data="edit_cover")],
    [InlineKeyboardButton(text="✅ Отправить", callback_data="send_audio")],
])
