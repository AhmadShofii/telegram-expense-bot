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
# STATISTICS
# ============================================================

from app.handlers.statistics import (
    statistics_command,
    statistics_chart_handler,
)


# ============================================================
# EXPORT
# ============================================================

from app.handlers.export import (
    export_command,
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
    edit_expense_text,
    delete_expense_confirmation_handler,
    delete_expense_handler,
    delete_expense_cancel_handler,
)


# ============================================================
# BUDGET
# ============================================================

from app.handlers.budget import (
    budget_command,
    budget_set_handler,
    budget_edit_handler,
    budget_input,
)


# ============================================================
# DATABASE
# ============================================================

from database.db import init_db


# ============================================================
# TEXT ROUTER
# ============================================================

async def text_router(
    update: Update,
    context,
):

    """
    Mengatur pesan text berdasarkan state user.

    Prioritas:

    1. Input budget
    2. Edit transaksi tersimpan
    3. Edit receipt
    4. Input transaksi manual
    """

    # ========================================================
    # BUDGET INPUT
    # ========================================================

    if context.user_data.get(
        "budget_input_mode"
    ):

        handled = await budget_input(
            update,
            context,
        )

        if handled:

            return

    # ========================================================
    # SAVED EXPENSE EDIT
    # ========================================================

    if context.user_data.get(
        "editing_expense_field"
    ):

        handled = await edit_expense_text(
            update,
            context,
        )

        if handled:

            return

    # ========================================================
    # RECEIPT EDIT
    # ========================================================

    receipt_edit_state = (
        context.user_data.get(
            "editing_receipt_field"
        )
    )

    if receipt_edit_state:

        await receipt_edit_text(
            update,
            context,
        )

        return

    # ========================================================
    # MANUAL EXPENSE
    # ========================================================

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
    # STATISTICS
    # ========================================================

    application.add_handler(
        CommandHandler(
            "statistik",
            statistics_command,
        )
    )

    application.add_handler(
        statistics_chart_handler
    )

    # ========================================================
    # EXPORT
    # ========================================================

    application.add_handler(
        CommandHandler(
            "export",
            export_command,
        )
    )

    # ========================================================
    # BUDGET
    # ========================================================

    application.add_handler(
        CommandHandler(
            "budget",
            budget_command,
        )
    )

    application.add_handler(
        budget_set_handler
    )

    application.add_handler(
        budget_edit_handler
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
    # EXPENSE CALLBACK
    # ========================================================

    application.add_handler(
        expense_callback_handler
    )

    # ========================================================
    # ALL TEXT INPUT
    # ========================================================

    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            text_router,
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