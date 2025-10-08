from aiogram.exceptions import TelegramAPIError

from app.bot import dp, bot
import asyncio
# from app.middlewares.auth import RegisterUserMiddleware
from app.db.models import Base
from app.db.session import engine
from app.services.init_db import init_db

async def main():
    print("🚀 Bot is starting...")
    Base.metadata.create_all(bind=engine)
    await init_db()
    from app.handlers import editor, user
    # dp.update.middleware(RegisterUserMiddleware())
    dp.include_router(editor.router)
    dp.include_router(user.router)
    print("✅ Bot is up and running!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("👋 Bot stopped.")
    except asyncio.CancelledError:
        print("🛑 Polling was cancelled.")
    except TelegramAPIError as e:
        print(f"❌ Telegram API error: {e}")