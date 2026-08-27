from sqlalchemy import select

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
)

from database.db import SessionLocal
from database.models import Expense


# ============================================================
# FORMAT RUPIAH
# ============================================================

def format_rupiah(amount: int) -> str:
    return f"Rp{amount:,}".replace(",", ".")


# ============================================================
# CATEGORY ICON
# ============================================================

def category_icon(category: str) -> str:

    icons = {
        "Makanan": "🍜",
        "Transportasi": "🚗",
        "Belanja": "🛒",
        "Kesehatan": "💊",
        "Hiburan": "🎮",
        "Lainnya": "📦",
    }

    return icons.get(
        category,
        "📦",
    )


# ============================================================
# BUILD HISTORY MESSAGE
# ============================================================

def build_history_message(
    expenses,
    page: int,
) -> str:

    per_page = 5
    offset = page * per_page

    message = (
        "📋 *Riwayat Pengeluaran*\n\n"
    )

    for index, expense in enumerate(
        expenses,
        start=offset + 1,
    ):

        if expense.expense_date:

            date_text = (
                expense.expense_date.strftime(
                    "%d-%m-%Y"
                )
            )

        else:

            date_text = "--"

        icon = category_icon(
            expense.category
        )

        message += (
            f"*{index}. "
            f"{icon} {expense.description}*\n"
        )

        message += (
            f"   📅 {date_text}\n"
        )

        message += (
            f"   💰 "
            f"{format_rupiah(expense.amount)}\n"
        )

        message += (
            f"   🏷️ {expense.category}\n\n"
        )

    message += (
        f"📄 Halaman {page + 1}"
    )

    return message


# ============================================================
# BUILD NAVIGATION
# ============================================================

def build_navigation(
    page: int,
    has_next: bool,
):

    buttons = []

    if page > 0:

        buttons.append(
            InlineKeyboardButton(
                "⬅️ Sebelumnya",
                callback_data=(
                    f"history_page_{page - 1}"
                ),
            )
        )

    if has_next:

        buttons.append(
            InlineKeyboardButton(
                "➡️ Berikutnya",
                callback_data=(
                    f"history_page_{page + 1}"
                ),
            )
        )

    if not buttons:

        return None

    return InlineKeyboardMarkup(
        [buttons]
    )


# ============================================================
# SHOW HISTORY
# ============================================================

async def show_history(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    page: int = 0,
):

    if not update.effective_user:
        return

    user_id = (
        update.effective_user.id
    )

    per_page = 5

    offset = page * per_page

    db = SessionLocal()

    try:

        # Ambil 1 data ekstra untuk
        # mengetahui apakah ada halaman berikutnya.
        statement = (
            select(Expense)
            .where(
                Expense.user_id == user_id
            )
            .order_by(
                Expense.expense_date.desc(),
                Expense.created_at.desc(),
            )
            .offset(offset)
            .limit(per_page + 1)
        )

        expenses = db.scalars(
            statement
        ).all()

        has_next = (
            len(expenses)
            > per_page
        )

        expenses = expenses[
            :per_page
        ]

        # ====================================================
        # EMPTY
        # ====================================================

        if not expenses:

            message = (
                "📋 *Riwayat Pengeluaran*\n\n"
                "Belum ada transaksi."
            )

            if update.callback_query:

                await update.callback_query.edit_message_text(

                    message,

                    parse_mode="Markdown",

                )

            elif update.message:

                await update.message.reply_text(

                    message,

                    parse_mode="Markdown",

                )

            return

        # ====================================================
        # MESSAGE
        # ====================================================

        message = build_history_message(
            expenses,
            page,
        )

        # ====================================================
        # NAVIGATION
        # ====================================================

        markup = build_navigation(
            page,
            has_next,
        )

        # ====================================================
        # CALLBACK UPDATE
        # ====================================================

        if update.callback_query:

            await update.callback_query.edit_message_text(

                message,

                reply_markup=markup,

                parse_mode="Markdown",

            )

        # ====================================================
        # NORMAL MESSAGE
        # ====================================================

        elif update.message:

            await update.message.reply_text(

                message,

                reply_markup=markup,

                parse_mode="Markdown",

            )

    except Exception as error:

        print(
            "History error:"
        )

        print(
            repr(error)
        )

        error_message = (
            "❌ Terjadi kesalahan "
            "saat mengambil riwayat."
        )

        if update.callback_query:

            await update.callback_query.edit_message_text(
                error_message
            )

        elif update.message:

            await update.message.reply_text(
                error_message
            )

    finally:

        db.close()


# ============================================================
# /RIWAYAT
# ============================================================

async def history_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await show_history(
        update,
        context,
        page=0,
    )


# ============================================================
# HISTORY PAGINATION
# ============================================================

async def history_page(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    try:

        page = int(
            query.data.replace(
                "history_page_",
                "",
            )
        )

    except (
        ValueError,
        AttributeError,
    ):

        await query.answer(
            "Halaman tidak valid.",
            show_alert=True,
        )

        return

    if page < 0:
        page = 0

    await show_history(
        update,
        context,
        page=page,
    )


# ============================================================
# CALLBACK HANDLER
# ============================================================

history_callback_handler = (
    CallbackQueryHandler(
        history_page,
        pattern=r"^history_page_\d+$",
    )
)