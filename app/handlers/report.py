from datetime import datetime, time

from sqlalchemy import select

from telegram import Update
from telegram.ext import ContextTypes

from database.db import SessionLocal
from database.models import Expense


# ============================================================
# HELPER
# ============================================================

def format_rupiah(
    amount: int,
) -> str:

    return f"Rp{amount:,}".replace(
        ",",
        ".",
    )


def get_month_range():

    now = datetime.now()

    start_datetime = datetime(
        now.year,
        now.month,
        1,
    )

    if now.month == 12:

        next_month = datetime(
            now.year + 1,
            1,
            1,
        )

    else:

        next_month = datetime(
            now.year,
            now.month + 1,
            1,
        )

    return (
        start_datetime,
        next_month,
    )


# ============================================================
# /HARI
# ============================================================

async def daily_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:
        return

    if not update.message:
        return

    user_id = update.effective_user.id

    today = datetime.now().date()

    start_datetime = datetime.combine(
        today,
        time.min,
    )

    end_datetime = datetime.combine(
        today,
        time.max,
    )

    db = SessionLocal()

    try:

        statement = (
            select(Expense)
            .where(
                Expense.user_id == user_id,
                Expense.created_at >= start_datetime,
                Expense.created_at <= end_datetime,
            )
            .order_by(
                Expense.created_at.asc()
            )
        )

        expenses = db.scalars(
            statement
        ).all()

        if not expenses:

            await update.message.reply_text(
                "📊 *Pengeluaran Hari Ini*\n\n"
                "Belum ada pengeluaran "
                "yang tercatat hari ini.",
                parse_mode="Markdown",
            )

            return

        total = sum(
            expense.amount
            for expense in expenses
        )

        category_totals = {}

        for expense in expenses:

            category = expense.category

            category_totals[category] = (
                category_totals.get(
                    category,
                    0,
                )
                + expense.amount
            )

        message = (
            "📊 *Pengeluaran Hari Ini*\n\n"
            f"📅 "
            f"{today.strftime('%d-%m-%Y')}\n\n"
            "*Berdasarkan kategori:*\n"
        )

        for category, amount in (
            category_totals.items()
        ):

            message += (
                f"• {category}: "
                f"{format_rupiah(amount)}\n"
            )

        message += "\n"

        message += (
            f"💰 *Total: "
            f"{format_rupiah(total)}*\n\n"
            "*Detail transaksi:*\n"
        )

        for index, expense in enumerate(
            expenses,
            start=1,
        ):

            message += (
                f"{index}. "
                f"{expense.description} - "
                f"{format_rupiah(expense.amount)}\n"
            )

        await update.message.reply_text(
            message,
            parse_mode="Markdown",
        )

    finally:

        db.close()


# ============================================================
# /BULAN
# ============================================================

async def monthly_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:
        return

    if not update.message:
        return

    user_id = update.effective_user.id

    now = datetime.now()

    start_datetime, next_month = (
        get_month_range()
    )

    db = SessionLocal()

    try:

        statement = (
            select(Expense)
            .where(
                Expense.user_id == user_id,
                Expense.created_at >= start_datetime,
                Expense.created_at < next_month,
            )
            .order_by(
                Expense.created_at.asc()
            )
        )

        expenses = db.scalars(
            statement
        ).all()

        month_name = now.strftime(
            "%B %Y"
        )

        if not expenses:

            await update.message.reply_text(
                f"📊 *Pengeluaran "
                f"{month_name}*\n\n"
                "Belum ada pengeluaran "
                "yang tercatat bulan ini.",
                parse_mode="Markdown",
            )

            return

        total = sum(
            expense.amount
            for expense in expenses
        )

        category_totals = {}

        for expense in expenses:

            category = expense.category

            category_totals[category] = (
                category_totals.get(
                    category,
                    0,
                )
                + expense.amount
            )

        daily_average = (
            total // now.day
        )

        message = (
            f"📊 *Pengeluaran "
            f"{month_name}*\n\n"
            "*Berdasarkan kategori:*\n"
        )

        for category, amount in (
            category_totals.items()
        ):

            message += (
                f"• {category}: "
                f"{format_rupiah(amount)}\n"
            )

        message += "\n"

        message += (
            f"💰 *Total: "
            f"{format_rupiah(total)}*\n"
            f"🧾 Transaksi: "
            f"{len(expenses)}\n"
            f"📅 Rata-rata/hari: "
            f"{format_rupiah(daily_average)}"
        )

        await update.message.reply_text(
            message,
            parse_mode="Markdown",
        )

    finally:

        db.close()


# ============================================================
# /REKAP
# ============================================================

async def expense_summary(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:
        return

    if not update.message:
        return

    user_id = update.effective_user.id

    now = datetime.now()

    start_datetime, next_month = (
        get_month_range()
    )

    db = SessionLocal()

    try:

        statement = (
            select(Expense)
            .where(
                Expense.user_id == user_id,
                Expense.created_at >= start_datetime,
                Expense.created_at < next_month,
            )
        )

        expenses = db.scalars(
            statement
        ).all()

        if not expenses:

            await update.message.reply_text(
                "📊 *Rekap Pengeluaran*\n\n"
                "Belum ada pengeluaran "
                "pada bulan ini.",
                parse_mode="Markdown",
            )

            return

        category_totals = {}

        for expense in expenses:

            category = expense.category

            category_totals[category] = (
                category_totals.get(
                    category,
                    0,
                )
                + expense.amount
            )

        total = sum(
            expense.amount
            for expense in expenses
        )

        sorted_categories = sorted(
            category_totals.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        category_icons = {
            "Makanan": "🍜",
            "Transportasi": "🚗",
            "Belanja": "🛒",
            "Lainnya": "📦",
        }

        month_name = now.strftime(
            "%B %Y"
        )

        message = (
            "📊 *Rekap Pengeluaran*\n\n"
            f"📅 {month_name}\n\n"
        )

        for category, amount in (
            sorted_categories
        ):

            percentage = (
                amount / total * 100
            )

            icon = category_icons.get(
                category,
                "📦",
            )

            message += (
                f"{icon} *{category}*\n"
                f"{format_rupiah(amount)} "
                f"— {percentage:.1f}%\n\n"
            )

        message += (
            "────────────────────\n"
            f"💰 *Total: "
            f"{format_rupiah(total)}*\n"
            f"🧾 Transaksi: "
            f"{len(expenses)}"
        )

        await update.message.reply_text(
            message,
            parse_mode="Markdown",
        )

    finally:

        db.close()