from datetime import date

from sqlalchemy import func, select

from telegram import Update
from telegram.ext import ContextTypes

from database.db import SessionLocal
from database.models import Expense


# ============================================================
# MONTH NAMES
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

def format_rupiah(
    amount: int,
) -> str:

    if amount is None:
        amount = 0

    return (
        f"Rp{int(amount):,}"
        .replace(",", ".")
    )


# ============================================================
# GET CURRENT MONTH RANGE
# ============================================================

def get_current_month_range():

    today = date.today()

    start_date = date(
        today.year,
        today.month,
        1,
    )

    if today.month == 12:

        end_date = date(
            today.year + 1,
            1,
            1,
        )

    else:

        end_date = date(
            today.year,
            today.month + 1,
            1,
        )

    return (
        start_date,
        end_date,
    )


# ============================================================
# GET STATISTICS DATA
# ============================================================

def get_statistics(
    user_id: int,
):

    start_date, end_date = (
        get_current_month_range()
    )

    db = SessionLocal()

    try:

        # ====================================================
        # TOTAL EXPENSE
        # ====================================================

        total_statement = (
            select(
                func.coalesce(
                    func.sum(
                        Expense.amount
                    ),
                    0,
                )
            )
            .where(
                Expense.user_id == user_id,
                Expense.expense_date >= start_date,
                Expense.expense_date < end_date,
            )
        )

        total = db.scalar(
            total_statement
        )

        total = int(
            total or 0
        )

        # ====================================================
        # TOTAL TRANSACTION
        # ====================================================

        count_statement = (
            select(
                func.count(
                    Expense.id
                )
            )
            .where(
                Expense.user_id == user_id,
                Expense.expense_date >= start_date,
                Expense.expense_date < end_date,
            )
        )

        transaction_count = db.scalar(
            count_statement
        )

        transaction_count = int(
            transaction_count or 0
        )

        # ====================================================
        # CATEGORY
        # ====================================================

        category_statement = (
            select(
                Expense.category,
                func.sum(
                    Expense.amount
                ),
            )
            .where(
                Expense.user_id == user_id,
                Expense.expense_date >= start_date,
                Expense.expense_date < end_date,
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

        category_rows = db.execute(
            category_statement
        ).all()

        categories = []

        for category, amount in category_rows:

            amount = int(
                amount or 0
            )

            if total > 0:

                percentage = (
                    amount
                    / total
                    * 100
                )

            else:

                percentage = 0

            categories.append(
                {
                    "category": (
                        category
                        or "Lainnya"
                    ),
                    "amount": amount,
                    "percentage": percentage,
                }
            )

        # ====================================================
        # ACTIVE DAYS
        # ====================================================

        active_days_statement = (
            select(
                func.count(
                    func.distinct(
                        Expense.expense_date
                    )
                )
            )
            .where(
                Expense.user_id == user_id,
                Expense.expense_date >= start_date,
                Expense.expense_date < end_date,
            )
        )

        active_days = db.scalar(
            active_days_statement
        )

        active_days = int(
            active_days or 0
        )

        # ====================================================
        # AVERAGE
        # ====================================================

        if active_days > 0:

            average_per_day = (
                total
                / active_days
            )

        else:

            average_per_day = 0

        return {
            "total": total,
            "transaction_count": transaction_count,
            "categories": categories,
            "active_days": active_days,
            "average_per_day": average_per_day,
        }

    finally:

        db.close()


# ============================================================
# CATEGORY ICON
# ============================================================

def get_category_icon(
    category: str,
) -> str:

    icons = {

        "Makanan": "🍔",

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
# PROGRESS BAR
# ============================================================

def build_progress_bar(
    percentage: float,
) -> str:

    percentage = max(
        0,
        min(
            percentage,
            100,
        ),
    )

    total_blocks = 10

    filled = int(
        percentage
        / 100
        * total_blocks
    )

    empty = (
        total_blocks
        - filled
    )

    return (
        "█" * filled
        + "░" * empty
    )


# ============================================================
# BUILD STATISTICS MESSAGE
# ============================================================

def build_statistics_message(
    data: dict,
) -> str:

    today = date.today()

    month_name = MONTH_NAMES[
        today.month - 1
    ]

    total = data[
        "total"
    ]

    transaction_count = data[
        "transaction_count"
    ]

    categories = data[
        "categories"
    ]

    active_days = data[
        "active_days"
    ]

    average_per_day = data[
        "average_per_day"
    ]

    # ========================================================
    # NO DATA
    # ========================================================

    if transaction_count == 0:

        return (

            "📊 *Statistik Pengeluaran*\n\n"

            f"🗓️ {month_name} "
            f"{today.year}\n\n"

            "Belum ada pengeluaran "
            "pada bulan ini.\n\n"

            "💡 Mulai catat pengeluaran "
            "untuk melihat statistik."

        )

    # ========================================================
    # HEADER
    # ========================================================

    message = (

        "📊 *STATISTIK PENGELUARAN*\n\n"

        f"🗓️ {month_name} "
        f"{today.year}\n\n"

        "💰 *Total Pengeluaran*\n"

        f"{format_rupiah(total)}\n\n"

        "🧾 *Jumlah Transaksi*\n"

        f"{transaction_count} transaksi\n\n"

        "📈 *Berdasarkan Kategori*\n"

    )

    # ========================================================
    # CATEGORIES
    # ========================================================

    for item in categories:

        category = item[
            "category"
        ]

        amount = item[
            "amount"
        ]

        percentage = item[
            "percentage"
        ]

        icon = get_category_icon(
            category
        )

        bar = build_progress_bar(
            percentage
        )

        message += (

            f"{icon} *{category}*\n"

            f"{format_rupiah(amount)} "
            f"({percentage:.1f}%)\n"

            f"`{bar}`\n\n"

        )

    # ========================================================
    # TOP CATEGORY
    # ========================================================

    if categories:

        top_category = categories[
            0
        ]

        message += (

            "🏆 *Kategori Terbesar*\n"

            f"{get_category_icon(top_category['category'])} "
            f"{top_category['category']} — "
            f"{format_rupiah(top_category['amount'])}\n\n"

        )

    # ========================================================
    # AVERAGE
    # ========================================================

    message += (

        "💸 *Rata-rata Pengeluaran*\n"

        f"{format_rupiah(int(average_per_day))} "
        f"per hari aktif\n\n"

        f"📅 Pengeluaran tercatat "
        f"selama {active_days} hari."

    )

    return message


# ============================================================
# /STATISTIK
# ============================================================

async def statistics_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:

        return

    user_id = (
        update.effective_user.id
    )

    try:

        data = get_statistics(
            user_id
        )

        message = (
            build_statistics_message(
                data
            )
        )

        if update.message:

            await update.message.reply_text(

                message,

                parse_mode="Markdown",

            )

        elif update.callback_query:

            await update.callback_query.message.reply_text(

                message,

                parse_mode="Markdown",

            )

    except Exception as error:

        print(
            "Statistics error:"
        )

        print(
            repr(error)
        )

        if update.message:

            await update.message.reply_text(

                "❌ Terjadi kesalahan "
                "saat mengambil statistik."

            )