from datetime import date, datetime

from sqlalchemy import func, select

from telegram import Update
from telegram.ext import ContextTypes

from database.db import SessionLocal
from database.models import Expense


# ============================================================
# CONSTANT
# ============================================================

MONTH_NAMES = [
    "Januari",
    "Februari",
    "Maret",
    "April",
    "Mei",
    "Juni",
    "Juli",
    "Agustus",
    "September",
    "Oktober",
    "November",
    "Desember",
]


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
# MONTH NAME
# ============================================================

def get_month_name(
    month: int,
) -> str:

    if 1 <= month <= 12:
        return MONTH_NAMES[month - 1]

    return str(month)


# ============================================================
# MONTH RANGE
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
# PREVIOUS MONTH
# ============================================================

def get_previous_month(
    year: int,
    month: int,
):

    if month == 1:

        return (
            year - 1,
            12,
        )

    return (
        year,
        month - 1,
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
# GET CATEGORY REPORT
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
# CALCULATE MONTH COMPARISON
# ============================================================

def calculate_month_comparison(
    current_total: int,
    previous_total: int,
):

    difference = (
        current_total
        - previous_total
    )

    # --------------------------------------------------------
    # Jika bulan sebelumnya = 0
    # --------------------------------------------------------

    if previous_total == 0:

        if current_total == 0:

            percentage = 0.0

        else:

            percentage = None

    else:

        percentage = (
            difference
            / previous_total
            * 100
        )

    return (
        difference,
        percentage,
    )


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

        f"📆 "
        f"{today.strftime('%d-%m-%Y')}\n\n"

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

    month_name = get_month_name(
        today.month
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
# EXPENSE SUMMARY / REKAP
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

    current_year = today.year
    current_month = today.month

    # ========================================================
    # CURRENT MONTH
    # ========================================================

    results = get_category_report(

        user_id,

        current_year,

        current_month,

    )

    # ========================================================
    # PREVIOUS MONTH
    # ========================================================

    (
        previous_year,
        previous_month,
    ) = get_previous_month(

        current_year,

        current_month,

    )

    current_total = get_monthly_total(

        user_id,

        current_year,

        current_month,

    )

    previous_total = get_monthly_total(

        user_id,

        previous_year,

        previous_month,

    )

    # ========================================================
    # NO CURRENT DATA
    # ========================================================

    if not results:

        message = (

            "📊 *Rekap Pengeluaran*\n\n"

            f"🗓️ "
            f"{get_month_name(current_month)} "
            f"{current_year}\n\n"

            "Belum ada pengeluaran "
            "untuk bulan ini.\n\n"

        )

        # ----------------------------------------------------
        # Still show comparison
        # ----------------------------------------------------

        if previous_total > 0:

            message += (

                "📈 *Perbandingan Bulan*\n\n"

                f"{get_month_name(previous_month)} "
                f"{previous_year}: "
                f"{format_rupiah(previous_total)}\n"

                f"{get_month_name(current_month)} "
                f"{current_year}: "
                f"{format_rupiah(current_total)}\n\n"

                "🔻 Pengeluaran bulan ini "
                "lebih rendah karena belum "
                "ada transaksi."

            )

        if update.message:

            await update.message.reply_text(

                message,

                parse_mode="Markdown",

            )

        return

    # ========================================================
    # HEADER
    # ========================================================

    message = (

        "📊 *Rekap Pengeluaran*\n\n"

        f"🗓️ "
        f"{get_month_name(current_month)} "
        f"{current_year}\n\n"

        f"💰 *Total: "
        f"{format_rupiah(current_total)}*\n\n"

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

        if current_total > 0:

            percentage = (

                category_total
                / current_total
                * 100

            )

        else:

            percentage = 0

        icon = category_icon(
            category
        )

        message += (

            f"{icon} *{category}*\n"

            f"   "
            f"{format_rupiah(category_total)} "
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
        f"{format_rupiah(largest_total)}\n\n"

    )

    # ========================================================
    # MONTH COMPARISON
    # ========================================================

    (
        difference,
        percentage,
    ) = calculate_month_comparison(

        current_total,

        previous_total,

    )

    message += (
        "📈 *Perbandingan Bulan*\n\n"
    )

    message += (

        f"{get_month_name(previous_month)} "
        f"{previous_year}: "
        f"{format_rupiah(previous_total)}\n"

        f"{get_month_name(current_month)} "
        f"{current_year}: "
        f"{format_rupiah(current_total)}\n\n"

    )

    # ========================================================
    # COMPARISON RESULT
    # ========================================================

    if previous_total == 0:

        if current_total > 0:

            message += (

                "🆕 Belum ada data "
                "pengeluaran bulan sebelumnya."

            )

        else:

            message += (
                "➡️ Tidak ada perubahan."
            )

    elif difference > 0:

        message += (

            f"🔺 *Naik "
            f"{format_rupiah(difference)}* "

        )

        if percentage is not None:

            message += (

                f"("
                f"+{format_percentage(percentage)}"
                f")"

            )

    elif difference < 0:

        decrease = abs(
            difference
        )

        decrease_percentage = (
            abs(percentage)
            if percentage is not None
            else 0
        )

        message += (

            f"🔻 *Turun "
            f"{format_rupiah(decrease)}* "

            f"("
            f"-{format_percentage(decrease_percentage)}"
            f")"

        )

    else:

        message += (
            "➡️ *Sama dengan bulan sebelumnya.*"
        )

    # ========================================================
    # SEND
    # ========================================================

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
    # OPTIONAL DATE
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
    # GET EXPENSES
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

        int(
            expense.amount or 0
        )

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

    # ========================================================
    # SEND
    # ========================================================

    if update.message:

        await update.message.reply_text(

            message,

            parse_mode="Markdown",

        )