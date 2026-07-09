from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

meta_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✏️ Название", callback_data="edit_title"),
     InlineKeyboardButton(text="✏️ Исполнитель", callback_data="edit_artist")],
    [InlineKeyboardButton(text="🖼 Обложка", callback_data="edit_cover")],
    [InlineKeyboardButton(text="📁 В очередь", callback_data="add_to_batch")],
    [InlineKeyboardButton(text="✅ Отправить", callback_data="send_audio")],
])

batch_add_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📁 Добавить ещё файл", callback_data="batch_add_more")],
    [InlineKeyboardButton(text="✅ Готово, редактировать всё", callback_data="batch_done")],
])

batch_edit_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✏️ Название (для всех)", callback_data="batch_edit_title")],
    [InlineKeyboardButton(text="✏️ Исполнитель (для всех)", callback_data="batch_edit_artist")],
    [InlineKeyboardButton(text="🖼 Обложка (для всех)", callback_data="batch_edit_cover")],
    [InlineKeyboardButton(text="📤 Отправить всё", callback_data="batch_send")],
])
