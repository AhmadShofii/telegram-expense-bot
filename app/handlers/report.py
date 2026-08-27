from datetime import date, datetime

from sqlalchemy import select

from telegram import Update
from telegram.ext import ContextTypes

from database.db import SessionLocal
from database.models import Expense


# ============================================================
# FORMAT RUPIAH
# ============================================================

def format_rupiah(
    amount: int,
) -> str:

    return f"Rp{amount:,}".replace(
        ",",
        ".",
    )


# ============================================================
# PARSE DATE
# ============================================================

def parse_date(
    value: str,
):
    """
    Format yang didukung:

    25-07-2026
    25/07/2026
    25.07.2026
    """

    value = value.strip()

    formats = [
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d.%m.%Y",
    ]

    for fmt in formats:

        try:

            return datetime.strptime(
                value,
                fmt,
            ).date()

        except ValueError:

            continue

    return None


# ============================================================
# PARSE MONTH
# ============================================================

def parse_month(
    value: str,
):
    """
    Format yang didukung:

    07-2026
    07/2026
    """

    value = value.strip()

    formats = [
        "%m-%Y",
        "%m/%Y",
    ]

    for fmt in formats:

        try:

            return datetime.strptime(
                value,
                fmt,
            ).date()

        except ValueError:

            continue

    return None


# ============================================================
# GET MONTH RANGE
# ============================================================

def get_month_range(
    year: int,
    month: int,
):

    start_date = date(
        year,
        month,
        1,
    )

    if month == 12:

        next_month = date(
            year + 1,
            1,
            1,
        )

    else:

        next_month = date(
            year,
            month + 1,
            1,
        )

    return (
        start_date,
        next_month,
    )


# ============================================================
# CATEGORY SUMMARY
# ============================================================

def build_category_summary(
    expenses,
):

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

    return category_totals


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

    today = date.today()

    await send_date_report(
        update,
        today,
        "Pengeluaran Hari Ini",
    )


# ============================================================
# DATE REPORT CORE
# ============================================================

async def send_date_report(
    update: Update,
    report_date: date,
    title: str,
):

    if not update.message:

        return

    user_id = update.effective_user.id

    db = SessionLocal()

    try:

        statement = (
            select(Expense)
            .where(
                Expense.user_id == user_id,
                Expense.expense_date == report_date,
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

                f"📊 *{title}*\n\n"

                f"📅 "
                f"{report_date.strftime('%d-%m-%Y')}\n\n"

                "Belum ada pengeluaran "
                "pada tanggal tersebut.",

                parse_mode="Markdown",

            )

            return

        total = sum(
            expense.amount
            for expense in expenses
        )

        category_totals = (
            build_category_summary(
                expenses
            )
        )

        message = (

            f"📊 *{title}*\n\n"

            f"📅 "
            f"{report_date.strftime('%d-%m-%Y')}\n\n"

            "*Berdasarkan kategori:*\n"

        )

        for category, amount in (
            category_totals.items()
        ):

            message += (
                f"• {category}: "
                f"{format_rupiah(amount)}\n"
            )

        message += (

            "\n"
            f"💰 *Total: "
            f"{format_rupiah(total)}*\n"

            f"🧾 Transaksi: "
            f"{len(expenses)}\n\n"

            "*Detail transaksi:*\n"

        )

        for index, expense in enumerate(
            expenses,
            start=1,
        ):

            message += (

                f"{index}. "
                f"{expense.description} — "
                f"{format_rupiah(expense.amount)}\n"

            )

        await update.message.reply_text(
            message,
            parse_mode="Markdown",
        )

    finally:

        db.close()


# ============================================================
# /TANGGAL
# ============================================================

async def date_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:

        return

    # ========================================================
    # TANPA ARGUMEN
    # ========================================================

    if not context.args:

        await update.message.reply_text(

            "❌ Format tanggal belum diberikan.\n\n"

            "Contoh:\n"
            "`/tanggal 25-07-2026`\n\n"

            "Format lain:\n"
            "`/tanggal 25/07/2026`\n"
            "`/tanggal 25.07.2026`",

            parse_mode="Markdown",

        )

        return

    date_text = context.args[0]

    report_date = parse_date(
        date_text
    )

    if not report_date:

        await update.message.reply_text(

            "❌ Format tanggal tidak valid.\n\n"

            "Gunakan format:\n"
            "`/tanggal 25-07-2026`",

            parse_mode="Markdown",

        )

        return

    await send_date_report(
        update,
        report_date,
        "Pengeluaran Tanggal",
    )


# ============================================================
# /BULAN
# ============================================================

async def month_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:

        return

    # ========================================================
    # TANPA ARGUMEN
    # ========================================================

    if not context.args:

        today = date.today()

        await send_month_report(
            update,
            today.year,
            today.month,
        )

        return

    month_text = context.args[0]

    month_date = parse_month(
        month_text
    )

    if not month_date:

        await update.message.reply_text(

            "❌ Format bulan tidak valid.\n\n"

            "Contoh:\n"
            "`/bulan 07-2026`\n\n"

            "atau:\n"
            "`/bulan 07/2026`",

            parse_mode="Markdown",

        )

        return

    await send_month_report(
        update,
        month_date.year,
        month_date.month,
    )


# ============================================================
# MONTH REPORT CORE
# ============================================================

async def send_month_report(
    update: Update,
    year: int,
    month: int,
):

    if not update.message:

        return

    user_id = update.effective_user.id

    start_date, next_month = (
        get_month_range(
            year,
            month,
        )
    )

    db = SessionLocal()

    try:

        statement = (
            select(Expense)
            .where(
                Expense.user_id == user_id,
                Expense.expense_date >= start_date,
                Expense.expense_date < next_month,
            )
            .order_by(
                Expense.expense_date.asc(),
                Expense.created_at.asc(),
            )
        )

        expenses = db.scalars(
            statement
        ).all()

        month_name = start_date.strftime(
            "%B %Y"
        )

        if not expenses:

            await update.message.reply_text(

                f"📊 *Pengeluaran "
                f"{month_name}*\n\n"

                "Belum ada pengeluaran "
                "pada bulan tersebut.",

                parse_mode="Markdown",

            )

            return

        total = sum(
            expense.amount
            for expense in expenses
        )

        category_totals = (
            build_category_summary(
                expenses
            )
        )

        # ====================================================
        # RATA-RATA HARIAN
        # ====================================================

        today = date.today()

        if (
            year == today.year
            and month == today.month
        ):

            days_passed = today.day

        else:

            days_passed = (
                next_month - start_date
            ).days

        daily_average = (
            total // days_passed
        )

        # ====================================================
        # MESSAGE
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

        message += (

            "\n"
            f"💰 *Total: "
            f"{format_rupiah(total)}*\n"

            f"🧾 Transaksi: "
            f"{len(expenses)}\n"

            f"📅 Rata-rata/hari: "
            f"{format_rupiah(daily_average)}\n\n"

            "*Detail transaksi:*\n"

        )

        for index, expense in enumerate(
            expenses,
            start=1,
        ):

            if expense.expense_date:

                date_text = (
                    expense.expense_date.strftime(
                        "%d-%m"
                    )
                )

            else:

                date_text = "--"

            message += (

                f"{index}. "
                f"{date_text} — "
                f"{expense.description} — "
                f"{format_rupiah(expense.amount)}\n"

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

    today = date.today()

    await send_summary(
        update,
        today.year,
        today.month,
    )


# ============================================================
# SUMMARY CORE
# ============================================================

async def send_summary(
    update: Update,
    year: int,
    month: int,
):

    if not update.message:

        return

    user_id = update.effective_user.id

    start_date, next_month = (
        get_month_range(
            year,
            month,
        )
    )

    db = SessionLocal()

    try:

        statement = (
            select(Expense)
            .where(
                Expense.user_id == user_id,
                Expense.expense_date >= start_date,
                Expense.expense_date < next_month,
            )
        )

        expenses = db.scalars(
            statement
        ).all()

        if not expenses:

            await update.message.reply_text(

                "📊 *Rekap Pengeluaran*\n\n"

                "Belum ada pengeluaran "
                "pada bulan tersebut.",

                parse_mode="Markdown",

            )

            return

        category_totals = (
            build_category_summary(
                expenses
            )
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

            "Kesehatan": "💊",

            "Hiburan": "🎮",

            "Lainnya": "📦",

        }

        month_name = (
            start_date.strftime(
                "%B %Y"
            )
        )

        message = (

            "📊 *Rekap Pengeluaran*\n\n"

            f"📅 {month_name}\n\n"

        )

        for category, amount in (
            sorted_categories
        ):

            percentage = (
                amount
                / total
                * 100
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

        # ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

monthly_report = month_report