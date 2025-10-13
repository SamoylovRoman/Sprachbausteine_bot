from aiogram import Bot, Dispatcher
from aiogram.types import BotCommandScopeDefault
from bot_commands import user_commands

from app.config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)

async def on_startup(bot: Bot):
    await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())

dp = Dispatcher()