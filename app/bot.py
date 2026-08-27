from telegram import Update

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.config import TELEGRAM_BOT_TOKEN


# ============================================================
# START
# ============================================================

from app.handlers.start import (
    start_command,
)


# ============================================================
# MANUAL EXPENSE
# ============================================================

from app.handlers.expense import (
    expense_message,
    expense_callback_handler,
)


# ============================================================
# REPORT
# ============================================================

from app.handlers.report import (
    daily_report,
    monthly_report,
    expense_summary,
    date_report,
    month_report,
)


# ============================================================
# RECEIPT
# ============================================================

from app.handlers.receipt import (
    receipt_photo,
    receipt_callback_handler,
    receipt_edit_callback_handler,
    receipt_edit_field_callback_handler,
    receipt_edit_back_callback_handler,
    receipt_edit_text,
)


# ============================================================
# HISTORY
# ============================================================

from app.handlers.history import (
    history_command,
    history_callback_handler,
    delete_expense_confirmation_handler,
    delete_expense_handler,
    delete_expense_cancel_handler,
)


# ============================================================
# DATABASE
# ============================================================

from database.db import init_db


# ============================================================
# MAIN
# ============================================================

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
        .token(
            TELEGRAM_BOT_TOKEN
        )
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
    # REPORT - HARI
    # ========================================================

    application.add_handler(
        CommandHandler(
            "hari",
            daily_report,
        )
    )

    # ========================================================
    # REPORT - BULAN
    # ========================================================

    application.add_handler(
        CommandHandler(
            "bulan",
            month_report,
        )
    )

    # ========================================================
    # REPORT - REKAP
    # ========================================================

    application.add_handler(
        CommandHandler(
            "rekap",
            expense_summary,
        )
    )

    # ========================================================
    # REPORT - TANGGAL
    # ========================================================

    application.add_handler(
        CommandHandler(
            "tanggal",
            date_report,
        )
    )

    # ========================================================
    # HISTORY
    # ========================================================

    application.add_handler(
        CommandHandler(
            "riwayat",
            history_command,
        )
    )

    # ========================================================
    # HISTORY PAGINATION
    # ========================================================

    application.add_handler(
        history_callback_handler
    )

    # ========================================================
    # DELETE CONFIRMATION
    # ========================================================

    application.add_handler(
        delete_expense_confirmation_handler
    )

    # ========================================================
    # DELETE EXPENSE
    # ========================================================

    application.add_handler(
        delete_expense_handler
    )

    # ========================================================
    # DELETE CANCEL
    # ========================================================

    application.add_handler(
        delete_expense_cancel_handler
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
    # RECEIPT SAVE / CANCEL
    # ========================================================

    application.add_handler(
        receipt_callback_handler
    )

    # ========================================================
    # RECEIPT EDIT MENU
    # ========================================================

    application.add_handler(
        receipt_edit_callback_handler
    )

    # ========================================================
    # RECEIPT EDIT FIELD
    # ========================================================

    application.add_handler(
        receipt_edit_field_callback_handler
    )

    # ========================================================
    # RECEIPT EDIT BACK
    # ========================================================

    application.add_handler(
        receipt_edit_back_callback_handler
    )

    # ========================================================
    # RECEIPT EDIT TEXT
    # ========================================================

    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            receipt_edit_text,
        )
    )

    # ========================================================
    # MANUAL EXPENSE CALLBACK
    # ========================================================

    application.add_handler(
        expense_callback_handler
    )

    # ========================================================
    # MANUAL EXPENSE TEXT
    # ========================================================

    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
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


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()