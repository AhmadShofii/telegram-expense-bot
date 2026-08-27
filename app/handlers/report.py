from datetime import date, datetime

from sqlalchemy import func, select

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

    return CATEGORY_ICONS.get(
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
        return MONTH_NAMES[
            month - 1
        ]

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
# GET DAILY EXPENSES
# ============================================================

def get_daily_expenses(
    user_id: int,
    target_date: date,
):

    db = SessionLocal()

    try:

        statement = (
            select(Expense)
            .where(
                Expense.user_id == user_id,
                Expense.expense_date == target_date,
            )
            .order_by(
                Expense.created_at.desc()
            )
        )

        return db.scalars(
            statement
        ).all()

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
# GET MONTHLY EXPENSES
# ============================================================

def get_monthly_expenses(
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
            select(Expense)
            .where(
                Expense.user_id == user_id,

                Expense.expense_date
                >= start_date,

                Expense.expense_date
                < end_date,
            )
            .order_by(
                Expense.expense_date.desc(),
                Expense.created_at.desc(),
            )
        )

        return db.scalars(
            statement
        ).all()

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

    expenses = get_daily_expenses(
        user_id,
        today,
    )

    # ========================================================
    # NO DATA
    # ========================================================

    if not expenses:

        message = (

            "📅 *LAPORAN HARI INI*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"

            f"📆 "
            f"{today.strftime('%d-%m-%Y')}\n\n"

            "📭 *Belum ada pengeluaran*\n\n"

            "Belum ada transaksi yang "
            "tercatat hari ini.\n\n"

            "💡 Kamu bisa mencatat "
            "pengeluaran dengan mengirim:\n\n"

            "`Makan siang 25000`"

        )

    else:

        # ====================================================
        # HEADER
        # ====================================================

        message = (

            "📅 *LAPORAN HARI INI*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"

            f"📆 *{today.strftime('%d-%m-%Y')}*\n\n"

            "💸 *Total Pengeluaran*\n"
            f"*{format_rupiah(total)}*\n\n"

            f"🧾 *{len(expenses)} transaksi*\n\n"

            "━━━━━━━━━━━━━━━━━━━━\n\n"

            "📝 *DAFTAR PENGELUARAN*\n\n"

        )

        # ====================================================
        # EXPENSE LIST
        # ====================================================

        for index, expense in enumerate(
            expenses,
            start=1,
        ):

            category = (
                expense.category
                or "Lainnya"
            )

            icon = category_icon(
                category
            )

            description = (
                expense.description
                or "Transaksi"
            )

            message += (

                f"*{index}. {icon} "
                f"{description}*\n"

                f"   💵 "
                f"{format_rupiah(expense.amount)}\n"

                f"   🏷️ {category}\n\n"

            )

        message += (
            "━━━━━━━━━━━━━━━━━━━━"
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

    expenses = get_monthly_expenses(

        user_id,

        today.year,

        today.month,

    )

    month_name = get_month_name(
        today.month
    )

    # ========================================================
    # NO DATA
    # ========================================================

    if not expenses:

        message = (

            "📆 *LAPORAN BULANAN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"

            f"🗓️ *{month_name} "
            f"{today.year}*\n\n"

            "📭 *Belum ada pengeluaran*\n\n"

            "Belum ada transaksi yang "
            "tercatat pada bulan ini.\n\n"

            "💡 Mulai catat pengeluaran "
            "untuk melihat laporan "
            "bulanan kamu."

        )

    else:

        # ====================================================
        # HEADER
        # ====================================================

        message = (

            "📆 *LAPORAN BULANAN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"

            f"🗓️ *{month_name} "
            f"{today.year}*\n\n"

            "💸 *Total Pengeluaran*\n"
            f"*{format_rupiah(total)}*\n\n"

            f"🧾 *{len(expenses)} transaksi*\n\n"

            "━━━━━━━━━━━━━━━━━━━━\n\n"

            "📊 *RINGKASAN KATEGORI*\n\n"

        )

        # ====================================================
        # CATEGORY SUMMARY
        # ====================================================

        results = get_category_report(

            user_id,

            today.year,

            today.month,

        )

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

            progress = (
                build_progress_bar(
                    percentage
                )
            )

            message += (

                f"{icon} *{category}*\n"

                f"   💵 "
                f"{format_rupiah(category_total)}\n"

                f"   `{progress}` "
                f"{format_percentage(percentage)}\n\n"

            )

        # ====================================================
        # FOOTER
        # ====================================================

        message += (
            "━━━━━━━━━━━━━━━━━━━━\n\n"

            "💡 Gunakan `/statistik` "
            "untuk melihat analisis "
            "pengeluaran lebih lengkap."
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

    results = get_category_report(

        user_id,

        current_year,

        current_month,

    )

    current_total = get_monthly_total(

        user_id,

        current_year,

        current_month,

    )

    # ========================================================
    # NO DATA
    # ========================================================

    if not results:

        message = (

            "📊 *REKAP PENGELUARAN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"

            f"🗓️ *"
            f"{get_month_name(current_month)} "
            f"{current_year}*\n\n"

            "📭 *Belum ada pengeluaran*\n\n"

            "Belum ada transaksi yang "
            "tercatat untuk bulan ini.\n\n"

            "💡 Mulai catat pengeluaran "
            "untuk melihat rekap."

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

        "📊 *REKAP PENGELUARAN*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"

        f"🗓️ *"
        f"{get_month_name(current_month)} "
        f"{current_year}*\n\n"

        "💸 *TOTAL PENGELUARAN*\n"
        f"*{format_rupiah(current_total)}*\n\n"

        f"🏷️ *{len(results)} kategori*\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "🏆 *RINGKASAN KATEGORI*\n\n"

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

        progress = (
            build_progress_bar(
                percentage
            )
        )

        message += (

            f"{icon} *{category}*\n"

            f"💵 "
            f"{format_rupiah(category_total)}\n"

            f"`{progress}` "
            f"*{format_percentage(percentage)}*\n\n"

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

    largest_percentage = (

        largest_total
        / current_total
        * 100

        if current_total > 0
        else 0

    )

    largest_icon = category_icon(
        largest_category
    )

    message += (

        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "🏆 *PENGELUARAN TERBESAR*\n\n"

        f"{largest_icon} "
        f"*{largest_category}*\n"

        f"💵 "
        f"{format_rupiah(largest_total)}\n"

        f"📊 "
        f"{format_percentage(largest_percentage)} "
        f"dari total pengeluaran\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "💡 Gunakan `/statistik` "
        "untuk melihat analisis "
        "pengeluaran lebih detail."

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

                    "❌ *Format tanggal tidak valid*\n\n"

                    "Gunakan salah satu format:\n\n"

                    "`/tanggal 27-08-2026`\n"
                    "`/tanggal 27/08/2026`\n"
                    "`/tanggal 2026-08-27`",

                    parse_mode="Markdown",

                )

            return

        target_date = (
            parsed_date
        )

    # ========================================================
    # GET EXPENSES
    # ========================================================

    expenses = get_daily_expenses(

        user_id,

        target_date,

    )

    # ========================================================
    # NO DATA
    # ========================================================

    if not expenses:

        message = (

            "📅 *LAPORAN TANGGAL*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"

            f"📆 *"
            f"{target_date.strftime('%d-%m-%Y')}"
            f"*\n\n"

            "📭 *Tidak ada pengeluaran*\n\n"

            "Tidak ditemukan transaksi "
            "pada tanggal tersebut."

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

    # ========================================================
    # HEADER
    # ========================================================

    message = (

        "📅 *LAPORAN TANGGAL*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"

        f"📆 *"
        f"{target_date.strftime('%d-%m-%Y')}"
        f"*\n\n"

        "💸 *TOTAL PENGELUARAN*\n"
        f"*{format_rupiah(total)}*\n\n"

        f"🧾 *{len(expenses)} transaksi*\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "📝 *DAFTAR TRANSAKSI*\n\n"

    )

    # ========================================================
    # EXPENSE LIST
    # ========================================================

    for index, expense in enumerate(

        expenses,

        start=1,

    ):

        category = (
            expense.category
            or "Lainnya"
        )

        icon = category_icon(
            category
        )

        description = (
            expense.description
            or "Transaksi"
        )

        message += (

            f"*{index}. {icon} "
            f"{description}*\n"

            f"   💵 "
            f"{format_rupiah(expense.amount)}\n"

            f"   🏷️ {category}\n\n"

        )

    message += (
        "━━━━━━━━━━━━━━━━━━━━"
    )

    if update.message:

        await update.message.reply_text(

            message,

            parse_mode="Markdown",

        )


# ============================================================
# REPORT MENU
# ============================================================

def build_report_keyboard():

    keyboard = [

        [

            InlineKeyboardButton(
                "📅 Hari Ini",
                callback_data="report_today",
            ),

            InlineKeyboardButton(
                "📆 Bulan Ini",
                callback_data="report_month",
            ),

        ],

        [

            InlineKeyboardButton(
                "📊 Rekap",
                callback_data="report_summary",
            ),

            InlineKeyboardButton(
                "📈 Statistik",
                callback_data="report_statistics",
            ),

        ],

    ]

    return InlineKeyboardMarkup(
        keyboard
    )


# ============================================================
# REPORT MENU COMMAND
# ============================================================

async def report_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = (

        "📈 *LAPORAN PENGELUARAN*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "Pilih jenis laporan yang "
        "ingin kamu lihat.\n\n"

        "📅 *Hari Ini*\n"
        "Melihat semua pengeluaran "
        "hari ini.\n\n"

        "📆 *Bulan Ini*\n"
        "Melihat ringkasan pengeluaran "
        "bulan berjalan.\n\n"

        "📊 *Rekap*\n"
        "Melihat pengeluaran berdasarkan "
        "kategori.\n\n"

        "📈 *Statistik*\n"
        "Melihat analisis pengeluaran "
        "lebih lengkap."

    )

    keyboard = (
        build_report_keyboard()
    )

    if update.message:

        await update.message.reply_text(

            message,

            reply_markup=keyboard,

            parse_mode="Markdown",

        )


# ============================================================
# REPORT CALLBACK
# ============================================================

async def report_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:

        return

    await query.answer()

    if query.data == "report_today":

        await query.message.reply_text(
            "📅 Menampilkan laporan hari ini..."
        )

        await daily_report(
            update,
            context,
        )

        return

    if query.data == "report_month":

        await query.message.reply_text(
            "📆 Menampilkan laporan bulan ini..."
        )

        await monthly_report(
            update,
            context,
        )

        return

    if query.data == "report_summary":

        await query.message.reply_text(
            "📊 Menampilkan rekap pengeluaran..."
        )

        await expense_summary(
            update,
            context,
        )

        return

    if query.data == "report_statistics":

        await query.message.reply_text(

            "📈 Gunakan `/statistik` "
            "untuk melihat statistik "
            "pengeluaran.",

            parse_mode="Markdown",

        )

        return


# ============================================================
# CALLBACK HANDLER
# ============================================================

report_callback_handler = (
    CallbackQueryHandler(

        report_callback,

        pattern=(
            r"^report_"
            r"(today|month|summary|statistics)$"
        ),

    )
)