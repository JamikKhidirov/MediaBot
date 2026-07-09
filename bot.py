import asyncio
import logging

from aiogram.types import BotCommand, BotCommandScopeDefault

from app.loader import bot, dp
import app.handlers  # noqa: F401

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    await bot.set_my_commands([
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="history", description="Последние 5 песен"),
        BotCommand(command="cancel", description="Отменить"),
    ], scope=BotCommandScopeDefault())
    try:
        await bot.set_my_name(name="MediaShtormBot")
        await bot.set_my_description(description="🎵 Редактор MP3: меняй название, исполнителя и обложку прямо в памяти. Пакетная обработка, история изменений.")
        await bot.set_my_short_description(short_description="🎵 Редактор MP3 — меняй название, исполнителя и обложку")
    except Exception as e:
        logger.warning("Не удалось установить имя/описание бота: %s", e)
    logger.info("AudioEditor запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
