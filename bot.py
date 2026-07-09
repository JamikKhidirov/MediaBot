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
        BotCommand(command="cancel", description="Отменить"),
    ], scope=BotCommandScopeDefault())
    logger.info("AudioEditor запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
