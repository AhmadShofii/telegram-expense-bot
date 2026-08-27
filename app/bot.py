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
    expense_summary,
)

from database.db import init_db


def main():
    # ==========================================
    # INISIALISASI DATABASE
    # ==========================================

    init_db()

    # ==========================================
    # MEMBUAT APLIKASI TELEGRAM
    # ==========================================

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    # ==========================================
    # COMMAND /start
    # ==========================================

    application.add_handler(
        CommandHandler(
            "start",
            start_command,
        )
    )

    # ==========================================
    # COMMAND /hari
    # ==========================================

    application.add_handler(
        CommandHandler(
            "hari",
            daily_report,
        )
    )

    # ==========================================
    # COMMAND /bulan
    # ==========================================

    application.add_handler(
        CommandHandler(
            "bulan",
            monthly_report,
        )
    )

    # ==========================================
    # COMMAND /rekap
    # ==========================================

    application.add_handler(
        CommandHandler(
            "rekap",
            expense_summary,
        )
    )

    # ==========================================
    # PESAN TEKS
    # ==========================================

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            expense_message,
        )
    )

    # ==========================================
    # CALLBACK BUTTON
    # ==========================================

    application.add_handler(
        expense_callback_handler
    )

    # ==========================================
    # RUN BOT
    # ==========================================

    print(
        "🤖 Expense Bot sedang berjalan..."
    )

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()