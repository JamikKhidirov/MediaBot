# AudioEditor Bot

Telegram-бот для редактирования метаданных MP3-файлов прямо в памяти — ничего не сохраняется на диск.

## Возможности

- **✏️ Редактирование названия** — меняй ID3-тег TIT2
- **✏️ Редактирование исполнителя** — меняй ID3-тег TPE1
- **🖼 Смена обложки** — отправь фото, оно станет обложкой трека
- **📁 Пакетная обработка** — добавь несколько файлов в очередь и изменить у всех название/исполнителя разом
- **📜 История** — `/history` показывает последние 5 отредактированных песен, можно скачать заново
- **🧠 Без сохранения на диск** — все операции в `BytesIO`

## Команды

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню |
| `/history` | Последние 5 отредактированных песен |
| `/cancel` | Отменить текущее действие |

## Установка

```bash
# Клонировать
git clone https://github.com/JamikKhidirov/MediaBot.git
cd MediaBot

# Создать виртуальное окружение
python -m venv .venv
.venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt

# Настроить токен
echo BOT_TOKEN=your_token_here > .env

# Запустить
python bot.py
```

## Зависимости

- `aiogram` — Telegram Bot API
- `mutagen` — работа с ID3-тегами MP3
- `python-dotenv` — загрузка `.env`

## Структура

```
MediaBot/
├── bot.py                  # Точка входа
├── requirements.txt
├── .env                    # Токен (не в git)
├── .gitignore
└── app/
    ├── config.py           # Загрузка токена
    ├── loader.py           # Bot + Dispatcher
    ├── states.py           # FSM-состояния
    ├── keyboards.py        # Inline-клавиатуры
    ├── services/
    │   ├── metadata.py     # Чтение/запись ID3-тегов (mutagen)
    │   └── history.py      # Хранение истории в памяти
    └── handlers/
        ├── start.py        # /start, /cancel, /history
        └── media.py        # Обработка MP3, пакетная обработка
```
