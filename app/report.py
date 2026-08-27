from datetime import datetime, time

from sqlalchemy import select

from telegram import Update
from telegram.ext import ContextTypes

from database.db import SessionLocal
from database.models import Expense


# ============================================================
# HELPER
# ============================================================

def format_rupiah(amount: int) -> str:
    """
    Mengubah angka menjadi format Rupiah.

    Contoh:
    25000 -> Rp25.000
    1000000 -> Rp1.000.000
    """
    return f"Rp{amount:,}".replace(",", ".")


def get_month_range():
    """
    Mengambil rentang waktu bulan berjalan.

    Return:
        start_datetime
        next_month
    """

    now = datetime.now()

    # Awal bulan
    start_datetime = datetime(
        now.year,
        now.month,
        1,
    )

    # Awal bulan berikutnya
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

    return start_datetime, next_month


# ============================================================
# /HARI
# ============================================================

async def daily_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Menampilkan seluruh pengeluaran user
    pada hari ini.
    """

    if not update.effective_user:
        return

    if not update.message:
        return

    user_id = update.effective_user.id

    today = datetime.now().date()

    # Awal hari
    start_datetime = datetime.combine(
        today,
        time.min,
    )

    # Akhir hari
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

        # Tidak ada transaksi
        if not expenses:
            await update.message.reply_text(
                "📊 *Pengeluaran Hari Ini*\n\n"
                "Belum ada pengeluaran "
                "yang tercatat hari ini.",
                parse_mode="Markdown",
            )
            return

        # ====================================================
        # TOTAL
        # ====================================================

        total = sum(
            expense.amount
            for expense in expenses
        )

        # ====================================================
        # KATEGORI
        # ====================================================

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

        # ====================================================
        # PESAN
        # ====================================================

        message = (
            "📊 *Pengeluaran Hari Ini*\n\n"
            f"📅 {today.strftime('%d-%m-%Y')}\n\n"
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


# ============================================================
# /BULAN
# ============================================================

async def monthly_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Menampilkan laporan pengeluaran
    pada bulan berjalan.
    """

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

        # Tidak ada transaksi
        if not expenses:
            await update.message.reply_text(
                f"📊 *Pengeluaran "
                f"{month_name}*\n\n"
                "Belum ada pengeluaran "
                "yang tercatat bulan ini.",
                parse_mode="Markdown",
            )
            return

        # ====================================================
        # TOTAL
        # ====================================================

        total = sum(
            expense.amount
            for expense in expenses
        )

        # ====================================================
        # KATEGORI
        # ====================================================

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

        # ====================================================
        # RATA-RATA PER HARI
        # ====================================================

        daily_average = (
            total // now.day
        )

        # ====================================================
        # PESAN
        # ====================================================

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
    """
    Menampilkan rekap pengeluaran berdasarkan kategori
    pada bulan berjalan.
    """

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

        # Tidak ada transaksi
        if not expenses:
            await update.message.reply_text(
                "📊 *Rekap Pengeluaran*\n\n"
                "Belum ada pengeluaran "
                "pada bulan ini.",
                parse_mode="Markdown",
            )
            return

        # ====================================================
        # TOTAL PER KATEGORI
        # ====================================================

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

        # ====================================================
        # TOTAL KESELURUHAN
        # ====================================================

        total = sum(
            expense.amount
            for expense in expenses
        )

        # ====================================================
        # URUTKAN TERBESAR
        # ====================================================

        sorted_categories = sorted(
            category_totals.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        # ====================================================
        # ICON KATEGORI
        # ====================================================

        category_icons = {
            "Makanan": "🍜",
            "Transportasi": "🚗",
            "Belanja": "🛒",
            "Lainnya": "📦",
        }

        # ====================================================
        # NAMA BULAN
        # ====================================================

        month_name = now.strftime(
            "%B %Y"
        )

        # ====================================================
        # PESAN
        # ====================================================

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