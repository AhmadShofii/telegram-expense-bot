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
    history_detail_handler,
    history_back_handler,

    expense_edit_handler,
    edit_field_handler,
    edit_cancel_handler,

    delete_expense_confirmation_handler,
    delete_expense_handler,
    delete_expense_cancel_handler,

    edit_expense_text,
)


# ============================================================
# DATABASE
# ============================================================

from database.db import init_db


# ============================================================
# EDIT TEXT ROUTER
# ============================================================

async def edit_text_router(
    update: Update,
    context,
):

    editing_expense = context.user_data.get(
        "editing_expense_field"
    )

    if editing_expense:

        handled = await edit_expense_text(
            update,
            context,
        )

        if handled:

            return

    await expense_message(
        update,
        context,
    )


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
    # HISTORY
    # ========================================================

    application.add_handler(
        CommandHandler(
            "riwayat",
            history_command,
        )
    )

    application.add_handler(
        history_callback_handler
    )

    application.add_handler(
        history_detail_handler
    )

    application.add_handler(
        history_back_handler
    )

    # ========================================================
    # EDIT SAVED EXPENSE
    # ========================================================

    application.add_handler(
        expense_edit_handler
    )

    application.add_handler(
        edit_field_handler
    )

    application.add_handler(
        edit_cancel_handler
    )

    # ========================================================
    # DELETE EXPENSE
    # ========================================================

    application.add_handler(
        delete_expense_confirmation_handler
    )

    application.add_handler(
        delete_expense_handler
    )

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
    # TEXT ROUTER
    #
    # Menangani:
    # - edit transaksi tersimpan
    # - edit receipt pending
    # - input expense manual
    # ========================================================

    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            edit_text_router,
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


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()