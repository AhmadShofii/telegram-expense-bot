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
    date_report,
    month_report,
)

from app.handlers.receipt import (
    receipt_photo,
    receipt_callback_handler,
)

from database.db import init_db


def main():

    # ========================================================
    # DATABASE
    # ========================================================

    init_db()

    # ========================================================
    # APPLICATION
    # ========================================================

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    # ========================================================
    # /START
    # ========================================================

    application.add_handler(
        CommandHandler(
            "start",
            start_command,
        )
    )

    # ========================================================
    # /HARI
    # ========================================================

    application.add_handler(
        CommandHandler(
            "hari",
            daily_report,
        )
    )

    # ========================================================
    # /BULAN
    # ========================================================

    application.add_handler(
        CommandHandler(
            "bulan",
            month_report,
        )
    )

    # ========================================================
    # /REKAP
    # ========================================================

    application.add_handler(
        CommandHandler(
            "rekap",
            expense_summary,
        )
    )

    # ========================================================
    # /TANGGAL
    # ========================================================

    application.add_handler(
        CommandHandler(
            "tanggal",
            date_report,
        )
    )

    # ========================================================
    # FOTO STRUK
    # ========================================================

    application.add_handler(
        MessageHandler(
            filters.PHOTO,
            receipt_photo,
        )
    )

    # ========================================================
    # CALLBACK STRUK
    # ========================================================

    application.add_handler(
        receipt_callback_handler
    )

    # ========================================================
    # CALLBACK EXPENSE MANUAL
    # ========================================================

    application.add_handler(
        expense_callback_handler
    )

    # ========================================================
    # TEXT MESSAGE
    # ========================================================

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            expense_message,
        )
    )

    # ========================================================
    # RUN
    # ========================================================

    print(
        "🤖 Expense Bot sedang berjalan..."
    )

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()