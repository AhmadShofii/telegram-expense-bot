from datetime import date, datetime

from sqlalchemy import (
    func,
    select,
)

from telegram import Update
from telegram.ext import ContextTypes

from database.db import SessionLocal
from database.models import Expense


# ============================================================
# FORMAT RUPIAH
# ============================================================

def format_rupiah(amount) -> str:

    if amount is None:
        amount = 0

    return (
        f"Rp{int(amount):,}"
        .replace(",", ".")
    )


# ============================================================
# FORMAT PERCENTAGE
# ============================================================

def format_percentage(
    value: float,
) -> str:

    return (
        f"{value:.1f}%"
        .replace(".", ",")
    )


# ============================================================
# CATEGORY ICON
# ============================================================

def category_icon(
    category: str,
) -> str:

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
# GET DATE RANGE
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

        end_date = date(
            year + 1,
            1,
            1,
        )

    else:

        end_date = date(
            year,
            month + 1,
            1,
        )

    return (
        start_date,
        end_date,
    )


# ============================================================
# GET DAILY TOTAL
# ============================================================

def get_daily_total(
    user_id: int,
    target_date: date,
):

    db = SessionLocal()

    try:

        statement = (
            select(
                func.coalesce(
                    func.sum(
                        Expense.amount
                    ),
                    0,
                )
            )
            .where(
                Expense.user_id
                == user_id,

                Expense.expense_date
                == target_date,
            )
        )

        result = db.scalar(
            statement
        )

        return int(
            result or 0
        )

    finally:

        db.close()


# ============================================================
# GET MONTHLY TOTAL
# ============================================================

def get_monthly_total(
    user_id: int,
    year: int,
    month: int,
):

    start_date, end_date = (
        get_month_range(
            year,
            month,
        )
    )

    db = SessionLocal()

    try:

        statement = (
            select(
                func.coalesce(
                    func.sum(
                        Expense.amount
                    ),
                    0,
                )
            )
            .where(
                Expense.user_id
                == user_id,

                Expense.expense_date
                >= start_date,

                Expense.expense_date
                < end_date,
            )
        )

        result = db.scalar(
            statement
        )

        return int(
            result or 0
        )

    finally:

        db.close()


# ============================================================
# DAILY REPORT
# ============================================================

async def daily_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:
        return

    user_id = (
        update.effective_user.id
    )

    today = date.today()

    total = get_daily_total(
        user_id,
        today,
    )

    message = (

        "📅 *Laporan Hari Ini*\n\n"

        f"📆 {today.strftime('%d-%m-%Y')}\n\n"

        f"💰 *Total Pengeluaran:*\n"
        f"{format_rupiah(total)}"

    )

    if update.message:

        await update.message.reply_text(

            message,

            parse_mode="Markdown",

        )


# ============================================================
# MONTHLY REPORT
# ============================================================

async def monthly_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:
        return

    user_id = (
        update.effective_user.id
    )

    today = date.today()

    total = get_monthly_total(

        user_id,

        today.year,

        today.month,

    )

    month_name = (
        today.strftime("%B")
    )

    message = (

        "📆 *Laporan Bulanan*\n\n"

        f"🗓️ {month_name} "
        f"{today.year}\n\n"

        f"💰 *Total Pengeluaran:*\n"
        f"{format_rupiah(total)}"

    )

    if update.message:

        await update.message.reply_text(

            message,

            parse_mode="Markdown",

        )


# ============================================================
# MONTH REPORT
# ============================================================

async def month_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await monthly_report(
        update,
        context,
    )


# ============================================================
# CATEGORY REPORT
# ============================================================

def get_category_report(
    user_id: int,
    year: int,
    month: int,
):

    start_date, end_date = (
        get_month_range(
            year,
            month,
        )
    )

    db = SessionLocal()

    try:

        statement = (

            select(

                Expense.category,

                func.sum(
                    Expense.amount
                ).label(
                    "total"
                ),

            )

            .where(

                Expense.user_id
                == user_id,

                Expense.expense_date
                >= start_date,

                Expense.expense_date
                < end_date,

            )

            .group_by(
                Expense.category
            )

            .order_by(
                func.sum(
                    Expense.amount
                ).desc()
            )

        )

        results = db.execute(
            statement
        ).all()

        return results

    finally:

        db.close()


# ============================================================
# EXPENSE SUMMARY
# ============================================================

async def expense_summary(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:
        return

    user_id = (
        update.effective_user.id
    )

    today = date.today()

    results = get_category_report(

        user_id,

        today.year,

        today.month,

    )

    # ========================================================
    # NO DATA
    # ========================================================

    if not results:

        message = (

            "📊 *Rekap Pengeluaran*\n\n"

            "Belum ada pengeluaran "
            "untuk bulan ini."

        )

        if update.message:

            await update.message.reply_text(

                message,

                parse_mode="Markdown",

            )

        return

    # ========================================================
    # TOTAL
    # ========================================================

    total = sum(

        int(row.total or 0)

        for row in results

    )

    # ========================================================
    # MESSAGE
    # ========================================================

    month_name = (
        today.strftime("%B")
    )

    message = (

        "📊 *Rekap Pengeluaran*\n\n"

        f"🗓️ {month_name} "
        f"{today.year}\n\n"

        f"💰 *Total: "
        f"{format_rupiah(total)}*\n\n"

    )

    # ========================================================
    # CATEGORY
    # ========================================================

    for row in results:

        category = (
            row.category
            or "Lainnya"
        )

        category_total = int(
            row.total or 0
        )

        if total > 0:

            percentage = (
                category_total
                / total
                * 100
            )

        else:

            percentage = 0

        icon = category_icon(
            category
        )

        message += (

            f"{icon} "
            f"*{category}*\n"

            f"   {format_rupiah(category_total)} "
            f"({format_percentage(percentage)})\n\n"

        )

    # ========================================================
    # LARGEST CATEGORY
    # ========================================================

    largest = results[0]

    largest_category = (
        largest.category
        or "Lainnya"
    )

    largest_total = int(
        largest.total or 0
    )

    largest_icon = category_icon(
        largest_category
    )

    message += (

        "🏆 *Pengeluaran Terbesar:*\n"

        f"{largest_icon} "
        f"{largest_category} — "
        f"{format_rupiah(largest_total)}"

    )

    if update.message:

        await update.message.reply_text(

            message,

            parse_mode="Markdown",

        )


# ============================================================
# DATE REPORT
# ============================================================

async def date_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:
        return

    user_id = (
        update.effective_user.id
    )

    # ========================================================
    # DEFAULT TODAY
    # ========================================================

    target_date = date.today()

    # ========================================================
    # OPTIONAL DATE ARGUMENT
    # ========================================================

    if context.args:

        date_text = (
            context.args[0]
        )

        formats = [

            "%d-%m-%Y",

            "%d/%m/%Y",

            "%Y-%m-%d",

        ]

        parsed_date = None

        for date_format in formats:

            try:

                parsed_date = (
                    datetime.strptime(
                        date_text,
                        date_format,
                    ).date()
                )

                break

            except ValueError:

                continue

        if parsed_date is None:

            if update.message:

                await update.message.reply_text(

                    "❌ Format tanggal tidak valid.\n\n"

                    "Contoh:\n"
                    "`/tanggal 27-08-2026`",

                    parse_mode="Markdown",

                )

            return

        target_date = (
            parsed_date
        )

    # ========================================================
    # QUERY
    # ========================================================

    db = SessionLocal()

    try:

        statement = (

            select(Expense)

            .where(

                Expense.user_id
                == user_id,

                Expense.expense_date
                == target_date,

            )

            .order_by(
                Expense.created_at.desc()
            )

        )

        expenses = db.scalars(
            statement
        ).all()

    finally:

        db.close()

    # ========================================================
    # NO DATA
    # ========================================================

    if not expenses:

        message = (

            "📅 *Laporan Tanggal*\n\n"

            f"📆 "
            f"{target_date.strftime('%d-%m-%Y')}\n\n"

            "Tidak ada pengeluaran."

        )

        if update.message:

            await update.message.reply_text(

                message,

                parse_mode="Markdown",

            )

        return

    # ========================================================
    # TOTAL
    # ========================================================

    total = sum(

        int(expense.amount or 0)

        for expense in expenses

    )

    message = (

        "📅 *Laporan Tanggal*\n\n"

        f"📆 "
        f"{target_date.strftime('%d-%m-%Y')}\n\n"

        f"💰 *Total: "
        f"{format_rupiah(total)}*\n\n"

    )

    # ========================================================
    # EXPENSE LIST
    # ========================================================

    for index, expense in enumerate(

        expenses,

        start=1,

    ):

        icon = category_icon(
            expense.category
        )

        message += (

            f"{index}. "
            f"{icon} "
            f"{expense.description}\n"

            f"   "
            f"{format_rupiah(expense.amount)}\n"

            f"   "
            f"{expense.category}\n\n"

        )

    if update.message:

        await update.message.reply_text(

            message,

            parse_mode="Markdown",

        )