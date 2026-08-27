import os
import tempfile
from datetime import date

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from sqlalchemy import func, select

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
    Update,
)

from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
)

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
# CATEGORY ICON
# ============================================================

CATEGORY_ICONS = {
    "Makanan": "🍜",
    "Transportasi": "🚗",
    "Belanja": "🛒",
    "Kesehatan": "💊",
    "Hiburan": "🎮",
    "Lainnya": "📦",
}


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
# CATEGORY ICON
# ============================================================

def get_category_icon(
    category: str,
) -> str:

    return CATEGORY_ICONS.get(
        category,
        "📦",
    )


# ============================================================
# CURRENT MONTH RANGE
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
# PROGRESS BAR
# ============================================================

def build_progress_bar(
    percentage: float,
    length: int = 10,
) -> str:

    percentage = max(
        0,
        min(
            percentage,
            100,
        ),
    )

    filled = int(
        percentage
        / 100
        * length
    )

    empty = (
        length - filled
    )

    return (
        "█" * filled
        + "░" * empty
    )


# ============================================================
# GET STATISTICS
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
        # TOTAL
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
        # TRANSACTION COUNT
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

            category = (
                category
                or "Lainnya"
            )

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
                    "category": category,
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
        # AVERAGE PER TRANSACTION
        # ====================================================

        if transaction_count > 0:

            average_per_transaction = (
                total
                / transaction_count
            )

        else:

            average_per_transaction = 0

        # ====================================================
        # AVERAGE PER ACTIVE DAY
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

            "transaction_count": (
                transaction_count
            ),

            "categories": categories,

            "active_days": active_days,

            "average_per_transaction": (
                average_per_transaction
            ),

            "average_per_day": (
                average_per_day
            ),

        }

    finally:

        db.close()


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

    average_per_transaction = data[
        "average_per_transaction"
    ]

    average_per_day = data[
        "average_per_day"
    ]

    # ========================================================
    # NO DATA
    # ========================================================

    if transaction_count == 0:

        return (

            "📊 *STATISTIK PENGELUARAN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"

            f"📅 *{month_name} "
            f"{today.year}*\n\n"

            "📭 *Belum ada data*\n\n"

            "Belum ada pengeluaran "
            "yang tercatat pada bulan ini.\n\n"

            "💡 Mulai catat pengeluaran "
            "untuk melihat statistik "
            "keuanganmu."

        )

    # ========================================================
    # HEADER
    # ========================================================

    message = (

        "📊 *STATISTIK PENGELUARAN*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"

        f"📅 *{month_name} "
        f"{today.year}*\n\n"

        "💸 *Total Pengeluaran*\n"
        f"*{format_rupiah(total)}*\n\n"

        "🧾 *Jumlah Transaksi*\n"
        f"*{transaction_count} transaksi*\n\n"

        "📈 *Rata-rata / Transaksi*\n"
        f"{format_rupiah(int(average_per_transaction))}\n\n"

        "📅 *Hari Aktif*\n"
        f"{active_days} hari\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "🏆 *PENGELUARAN BERDASARKAN "
        "KATEGORI*\n\n"

    )

    # ========================================================
    # CATEGORY
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

            f"💵 {format_rupiah(amount)}\n"

            f"`{bar}` "
            f"*{percentage:.1f}%*\n\n"

        )

    # ========================================================
    # TOP CATEGORY
    # ========================================================

    if categories:

        top_category = categories[
            0
        ]

        top_icon = get_category_icon(
            top_category["category"]
        )

        message += (

            "━━━━━━━━━━━━━━━━━━━━\n\n"

            "🏆 *KATEGORI TERBESAR*\n\n"

            f"{top_icon} "
            f"*{top_category['category']}*\n"

            f"💵 "
            f"{format_rupiah(top_category['amount'])}\n"

            f"📊 "
            f"{top_category['percentage']:.1f}% "
            f"dari total pengeluaran\n\n"

        )

    # ========================================================
    # AVERAGE
    # ========================================================

    message += (

        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "💡 *RINGKASAN*\n\n"

        f"💸 Rata-rata per transaksi: "
        f"{format_rupiah(int(average_per_transaction))}\n"

        f"📅 Rata-rata per hari aktif: "
        f"{format_rupiah(int(average_per_day))}\n\n"

        "Gunakan grafik untuk melihat "
        "perbandingan pengeluaran "
        "berdasarkan kategori."

    )

    return message


# ============================================================
# STATISTICS KEYBOARD
# ============================================================

def build_statistics_keyboard():

    keyboard = [

        [

            InlineKeyboardButton(

                "📈 Lihat Grafik",

                callback_data=(
                    "statistics_chart"
                ),

            ),

        ],

    ]

    return InlineKeyboardMarkup(
        keyboard
    )


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

        keyboard = (
            build_statistics_keyboard()
        )

        if update.message:

            await update.message.reply_text(

                message,

                reply_markup=keyboard,

                parse_mode="Markdown",

            )

        elif update.callback_query:

            if update.callback_query.message:

                await (
                    update.callback_query.message
                    .reply_text(

                        message,

                        reply_markup=keyboard,

                        parse_mode="Markdown",

                    )
                )

    except Exception as error:

        print(
            "❌ Statistics error:"
        )

        print(
            repr(error)
        )

        if update.message:

            await update.message.reply_text(

                "❌ Terjadi kesalahan "
                "saat mengambil statistik."

            )


# ============================================================
# CREATE EXPENSE CHART
# ============================================================

def create_expense_chart(
    user_id: int,
):

    data = get_statistics(
        user_id
    )

    categories = data[
        "categories"
    ]

    if not categories:

        return None

    labels = [

        item["category"]

        for item in categories

    ]

    values = [

        item["amount"]

        for item in categories

    ]

    today = date.today()

    month_name = MONTH_NAMES[
        today.month - 1
    ]

    # ========================================================
    # TEMP FILE
    # ========================================================

    temp_file = (
        tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False,
        )
    )

    chart_path = (
        temp_file.name
    )

    temp_file.close()

    # ========================================================
    # FIGURE
    # ========================================================

    figure = plt.figure(
        figsize=(9, 6)
    )

    axis = figure.add_subplot(
        111
    )

    axis.bar(
        labels,
        values,
    )

    axis.set_title(

        f"Pengeluaran Berdasarkan "
        f"Kategori\n"
        f"{month_name} {today.year}",

    )

    axis.set_xlabel(
        "Kategori"
    )

    axis.set_ylabel(
        "Nominal (Rp)"
    )

    axis.tick_params(
        axis="x",
        rotation=25,
    )

    # ========================================================
    # VALUE LABEL
    # ========================================================

    for index, value in enumerate(
        values
    ):

        axis.text(

            index,

            value,

            format_rupiah(
                value
            ),

            ha="center",

            va="bottom",

            fontsize=9,

        )

    figure.tight_layout()

    figure.savefig(

        chart_path,

        dpi=150,

        bbox_inches="tight",

    )

    plt.close(
        figure
    )

    return chart_path


# ============================================================
# SEND EXPENSE CHART
# ============================================================

async def statistics_chart_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:

        return

    await query.answer()

    if not update.effective_user:

        return

    if not query.message:

        return

    user_id = (
        update.effective_user.id
    )

    chart_path = None

    try:

        chart_path = (
            create_expense_chart(
                user_id
            )
        )

        if not chart_path:

            await query.message.reply_text(

                "📈 *GRAFIK PENGELUARAN*\n\n"

                "📭 Belum ada data "
                "pengeluaran untuk "
                "dibuat grafik.",

                parse_mode="Markdown",

            )

            return

        today = date.today()

        month_name = MONTH_NAMES[
            today.month - 1
        ]

        data = get_statistics(
            user_id
        )

        caption = (

            "📈 *GRAFIK PENGELUARAN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"

            f"📅 {month_name} "
            f"{today.year}\n\n"

            f"💸 Total: "
            f"*{format_rupiah(data['total'])}*\n"

            f"🧾 Transaksi: "
            f"*{data['transaction_count']}*\n\n"

            "Grafik menunjukkan "
            "pengeluaran berdasarkan "
            "kategori."

        )

        with open(
            chart_path,
            "rb",
        ) as chart_file:

            await query.message.reply_photo(

                photo=InputFile(

                    chart_file,

                    filename=(
                        "expense_chart.png"
                    ),

                ),

                caption=caption,

                parse_mode="Markdown",

            )

    except Exception as error:

        print(
            "❌ Chart error:"
        )

        print(
            repr(error)
        )

        await query.message.reply_text(

            "❌ Gagal membuat "
            "grafik pengeluaran."

        )

    finally:

        if chart_path:

            try:

                if os.path.exists(
                    chart_path
                ):

                    os.remove(
                        chart_path
                    )

            except OSError:

                pass


# ============================================================
# CALLBACK HANDLER
# ============================================================

statistics_chart_handler = (
    CallbackQueryHandler(

        statistics_chart_callback,

        pattern=(
            r"^statistics_chart$"
        ),

    )
)