from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
)

from app.config import TELEGRAM_BOT_TOKEN
from app.handlers.start import start_command


def main():
    application = Application.builder().token(
        TELEGRAM_BOT_TOKEN
    ).build()

    application.add_handler(
        CommandHandler("start", start_command)
    )

    print("🤖 Expense Bot sedang berjalan...")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()