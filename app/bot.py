from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
)

from app.config import TELEGRAM_BOT_TOKEN
from app.handlers.start import start_command
from database.db import init_db


def main():
    # Membuat database dan tabel jika belum tersedia
    init_db()

    # Membuat aplikasi Telegram
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    # Handler command /start
    application.add_handler(
        CommandHandler(
            "start",
            start_command,
        )
    )

    print("🤖 Expense Bot sedang berjalan...")

    # Menjalankan bot
    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()