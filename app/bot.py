from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.config import TELEGRAM_BOT_TOKEN

from app.handlers.start import start_command

from app.handlers.expense import (
    expense_message,
    expense_callback_handler,
)

from app.handlers.report import (
    daily_report,
    monthly_report,
)

from database.db import init_db


def main():
    # Inisialisasi database
    init_db()

    # Membuat aplikasi Telegram
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    # =========================
    # COMMAND HANDLERS
    # =========================

    # /start
    application.add_handler(
        CommandHandler(
            "start",
            start_command,
        )
    )

    # /hari
    application.add_handler(
        CommandHandler(
            "hari",
            daily_report,
        )
    )

    # /bulan
    application.add_handler(
        CommandHandler(
            "bulan",
            monthly_report,
        )
    )

    # =========================
    # MESSAGE HANDLERS
    # =========================

    # Pesan teks untuk mencatat pengeluaran
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            expense_message,
        )
    )

    # Tombol Simpan / Batal
    application.add_handler(
        expense_callback_handler
    )

    print(
        "🤖 Expense Bot sedang berjalan..."
    )

    # Menjalankan bot
    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()