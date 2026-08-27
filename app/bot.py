from telegram import (
    BotCommand,
    BotCommandScopeAllPrivateChats,
    MenuButtonCommands,
    Update,
)

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
# HELP
# ============================================================

from app.handlers.help import (
    menu_command,
    bantuan_command,
    help_callback_handler,
)


# ============================================================
# REMINDER
# ============================================================

from app.handlers.reminder import (
    reminder_command,
    reminder_handler,
    reminder_time_handler,
    reminder_status_handler,
    reminder_off_handler,
    reminder_back_handler,
    restore_reminders,
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
# TELEGRAM COMMAND MENU
# ============================================================

async def post_init(
    application: Application,
):

    commands = [

        BotCommand(
            "start",
            "Mulai menggunakan bot",
        ),

        BotCommand(
            "menu",
            "Tampilkan menu utama",
        ),

        BotCommand(
            "bantuan",
            "Panduan penggunaan bot",
        ),

        BotCommand(
            "riwayat",
            "Lihat riwayat pengeluaran",
        ),

        BotCommand(
            "hari",
            "Laporan pengeluaran hari ini",
        ),

        BotCommand(
            "tanggal",
            "Laporan berdasarkan tanggal",
        ),

        BotCommand(
            "bulan",
            "Laporan pengeluaran bulan ini",
        ),

        BotCommand(
            "rekap",
            "Rekap pengeluaran bulan ini",
        ),

        BotCommand(
            "budget",
            "Lihat dan kelola budget",
        ),

        BotCommand(
            "statistik",
            "Lihat statistik pengeluaran",
        ),

        BotCommand(
            "export",
            "Export laporan ke CSV",
        ),

        BotCommand(
            "reminder",
            "Atur pengingat harian",
        ),

    ]

    try:

        # ====================================================
        # TELEGRAM COMMANDS
        # ====================================================

        await application.bot.set_my_commands(

            commands=commands,

            scope=(
                BotCommandScopeAllPrivateChats()
            ),

        )

        # ====================================================
        # MENU BUTTON
        # ====================================================

        await application.bot.set_chat_menu_button(

            menu_button=MenuButtonCommands()

        )

        # ====================================================
        # VERIFY COMMANDS
        # ====================================================

        registered_commands = (

            await application.bot.get_my_commands(

                scope=(
                    BotCommandScopeAllPrivateChats()
                )

            )

        )

        print(
            "========================================"
        )

        print(
            "✅ Telegram command menu berhasil diatur."
        )

        print(
            "========================================"
        )

        print(
            "📋 Commands yang terdaftar:"
        )

        for command in registered_commands:

            print(

                f"   /{command.command} "
                f"- {command.description}"

            )

        print(
            "========================================"
        )

        print(
            "✅ Menu Button Telegram berhasil diatur."
        )

        print(
            "========================================"
        )

        # ====================================================
        # RESTORE REMINDER
        # ====================================================

        restore_reminders(
            application
        )

    except Exception as error:

        print(
            "========================================"
        )

        print(
            "❌ Gagal pada proses startup:"
        )

        print(
            repr(error)
        )

        print(
            "========================================"
        )


# ============================================================
# TEXT ROUTER
# ============================================================

async def text_router(
    update: Update,
    context,
):

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
    #
    # IMPORTANT:
    # receipt.py menggunakan:
    #
    # "editing_receipt_field"
    #
    # BUKAN:
    #
    # "receipt_edit_field"
    #
    # ========================================================

    if context.user_data.get(
        "editing_receipt_field"
    ):

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

        .post_init(
            post_init
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
    # MENU
    # ========================================================

    application.add_handler(

        CommandHandler(
            "menu",
            menu_command,
        )

    )

    # ========================================================
    # BANTUAN
    # ========================================================

    application.add_handler(

        CommandHandler(
            "bantuan",
            bantuan_command,
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
    # REMINDER
    # ========================================================

    application.add_handler(

        CommandHandler(
            "reminder",
            reminder_command,
        )

    )

    application.add_handler(
        reminder_handler
    )

    application.add_handler(
        reminder_time_handler
    )

    application.add_handler(
        reminder_status_handler
    )

    application.add_handler(
        reminder_off_handler
    )

    application.add_handler(
        reminder_back_handler
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
    # EDIT EXPENSE
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
    # HELP CALLBACK
    # ========================================================

    application.add_handler(
        help_callback_handler
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

    print(
        "========================================"
    )

    print(
        "🚀 Semua handler berhasil dimuat."
    )

    print(
        "========================================"
    )

    application.run_polling(

        allowed_updates=Update.ALL_TYPES

    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()