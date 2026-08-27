from telegram import Update

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.config import TELEGRAM_BOT_TOKEN

from app.handlers.start import (
    start_command,
)

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
    receipt_edit_callback_handler,
    receipt_edit_field_callback_handler,
    receipt_edit_back_callback_handler,
    receipt_edit_text,
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
    # START
    # ========================================================

    application.add_handler(
        CommandHandler(
            "start",
            start_command,
        )
    )

    # ========================================================
    # REPORT
    # ========================================================

    application.add_handler(
        CommandHandler(
            "hari",
            daily_report,
        )
    )

    application.add_handler(
        CommandHandler(
            "bulan",
            month_report,
        )
    )

    application.add_handler(
        CommandHandler(
            "rekap",
            expense_summary,
        )
    )

    application.add_handler(
        CommandHandler(
            "tanggal",
            date_report,
        )
    )

    # ========================================================
    # RECEIPT PHOTO
    # ========================================================

    application.add_handler(
        MessageHandler(
            filters.PHOTO,
            receipt_photo,
        )
    )

    # ========================================================
    # RECEIPT CALLBACK
    # ========================================================

    application.add_handler(
        receipt_callback_handler
    )

    application.add_handler(
        receipt_edit_callback_handler
    )

    application.add_handler(
        receipt_edit_field_callback_handler
    )

    application.add_handler(
        receipt_edit_back_callback_handler
    )

    # ========================================================
    # RECEIPT EDIT TEXT
    #
    # Harus diletakkan sebelum expense_message.
    # Jika bukan mode edit, receipt_edit_text langsung return.
    # ========================================================

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receipt_edit_text,
        )
    )

    # ========================================================
    # MANUAL EXPENSE
    # ========================================================

    application.add_handler(
        expense_callback_handler
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            expense_message,
        )
    )

    # ========================================================
    # RUN BOT
    # ========================================================

    print(
        "🤖 Expense Bot sedang berjalan..."
    )

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()