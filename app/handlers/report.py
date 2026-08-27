from datetime import datetime, time

from sqlalchemy import select, func
from telegram import Update
from telegram.ext import ContextTypes

from database.db import SessionLocal
from database.models import Expense


def format_rupiah(amount: int) -> str:
    return f"Rp{amount:,}".replace(",", ".")


async def daily_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.effective_user or not update.message:
        return

    user_id = update.effective_user.id

    # Awal dan akhir hari ini
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
        # Ambil seluruh pengeluaran user hari ini
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

        expenses = db.scalars(statement).all()

        if not expenses:
            await update.message.reply_text(
                "📊 *Pengeluaran Hari Ini*\n\n"
                "Belum ada pengeluaran yang tercatat hari ini.",
                parse_mode="Markdown",
            )
            return

        # Hitung total
        total = sum(
            expense.amount
            for expense in expenses
        )

        # Hitung berdasarkan kategori
        category_totals = {}

        for expense in expenses:
            category = expense.category

            category_totals[category] = (
                category_totals.get(category, 0)
                + expense.amount
            )

        # Buat pesan laporan
        message = (
            "📊 *Pengeluaran Hari Ini*\n\n"
        )

        message += (
            f"📅 {today.strftime('%d-%m-%Y')}\n\n"
        )

        message += "*Berdasarkan kategori:*\n"

        for category, amount in category_totals.items():
            message += (
                f"• {category}: "
                f"{format_rupiah(amount)}\n"
            )

        message += "\n"

        message += (
            f"💰 *Total: {format_rupiah(total)}*\n\n"
        )

        message += "*Detail transaksi:*\n"

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