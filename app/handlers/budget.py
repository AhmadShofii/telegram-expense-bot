from datetime import date

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
from database.models import Budget, Expense


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
# MONTH NAME
# ============================================================

def get_month_name(month: int) -> str:

    return MONTH_NAMES[month - 1]


# ============================================================
# GET CURRENT BUDGET
# ============================================================

def get_current_budget(
    user_id: int,
):

    today = date.today()

    db = SessionLocal()

    try:

        statement = (
            select(Budget)
            .where(
                Budget.user_id == user_id,
                Budget.year == today.year,
                Budget.month == today.month,
            )
        )

        return db.scalar(
            statement
        )

    finally:

        db.close()


# ============================================================
# GET CURRENT EXPENSE TOTAL
# ============================================================

def get_current_expense_total(
    user_id: int,
):

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
                Expense.user_id == user_id,
                Expense.expense_date >= start_date,
                Expense.expense_date < end_date,
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
# BUILD PROGRESS BAR
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

    filled_blocks = int(
        percentage
        / 100
        * total_blocks
    )

    empty_blocks = (
        total_blocks
        - filled_blocks
    )

    return (
        "█" * filled_blocks
        + "░" * empty_blocks
    )


# ============================================================
# BUILD BUDGET MESSAGE
# ============================================================

def build_budget_message(
    budget,
    expense_total: int,
) -> str:

    today = date.today()

    month_name = get_month_name(
        today.month
    )

    budget_amount = int(
        budget.amount
    )

    remaining = (
        budget_amount
        - expense_total
    )

    if budget_amount > 0:

        percentage = (
            expense_total
            / budget_amount
            * 100
        )

    else:

        percentage = 0

    progress_bar = build_progress_bar(
        percentage
    )

    if percentage >= 100:

        status = (
            "🔴 *Budget terlampaui!*"
        )

    elif percentage >= 80:

        status = (
            "🟡 *Peringatan! "
            "Budget hampir habis.*"
        )

    else:

        status = (
            "🟢 *Budget masih aman.*"
        )

    if remaining >= 0:

        remaining_text = (
            format_rupiah(
                remaining
            )
        )

    else:

        remaining_text = (

            "-"
            + format_rupiah(
                abs(remaining)
            )

        )

    return (

        f"💰 *Budget "
        f"{month_name} "
        f"{today.year}*\n\n"

        f"Budget:\n"
        f"*{format_rupiah(budget_amount)}*\n\n"

        f"Pengeluaran:\n"
        f"*{format_rupiah(expense_total)}*\n\n"

        f"Sisa:\n"
        f"*{remaining_text}*\n\n"

        f"{progress_bar} "
        f"{percentage:.1f}%\n\n"

        f"{status}"

    )


# ============================================================
# BUILD BUDGET WARNING
# ============================================================

def build_budget_warning(
    user_id: int,
):
    """
    Menghasilkan pesan warning berdasarkan
    penggunaan budget bulan berjalan.

    Return:
        None  -> belum ada warning
        str   -> pesan warning
    """

    budget = get_current_budget(
        user_id
    )

    # --------------------------------------------------------
    # Belum ada budget
    # --------------------------------------------------------

    if not budget:

        return None

    expense_total = (
        get_current_expense_total(
            user_id
        )
    )

    budget_amount = int(
        budget.amount
    )

    if budget_amount <= 0:

        return None

    percentage = (
        expense_total
        / budget_amount
        * 100
    )

    # --------------------------------------------------------
    # Di bawah 80%
    # --------------------------------------------------------

    if percentage < 80:

        return None

    # --------------------------------------------------------
    # Budget terlampaui
    # --------------------------------------------------------

    if percentage >= 100:

        exceeded = (
            expense_total
            - budget_amount
        )

        return (

            "🔴 *Budget terlampaui!*\n\n"

            f"Budget: "
            f"{format_rupiah(budget_amount)}\n"

            f"Pengeluaran: "
            f"{format_rupiah(expense_total)}\n"

            f"Lebih: "
            f"{format_rupiah(exceeded)}"

        )

    # --------------------------------------------------------
    # 80% - 99%
    # --------------------------------------------------------

    remaining = (
        budget_amount
        - expense_total
    )

    return (

        "🟡 *Peringatan Budget*\n\n"

        f"Budget sudah terpakai "
        f"*{percentage:.1f}%*.\n\n"

        f"Budget: "
        f"{format_rupiah(budget_amount)}\n"

        f"Pengeluaran: "
        f"{format_rupiah(expense_total)}\n"

        f"Sisa: "
        f"{format_rupiah(remaining)}"

    )


# ============================================================
# GET BUDGET WARNING
# ============================================================

async def send_budget_warning(
    update: Update,
):
    """
    Mengirim warning budget setelah transaksi berhasil
    disimpan.
    """

    if not update.effective_user:

        return

    user_id = (
        update.effective_user.id
    )

    warning = build_budget_warning(
        user_id
    )

    if not warning:

        return

    if update.message:

        await update.message.reply_text(

            warning,

            parse_mode="Markdown",

        )


# ============================================================
# SHOW BUDGET
# ============================================================

async def show_budget(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:

        return

    user_id = (
        update.effective_user.id
    )

    budget = get_current_budget(
        user_id
    )

    # --------------------------------------------------------
    # BELUM ADA BUDGET
    # --------------------------------------------------------

    if not budget:

        today = date.today()

        month_name = get_month_name(
            today.month
        )

        message = (

            "💰 *Budget Bulanan*\n\n"

            f"🗓️ {month_name} "
            f"{today.year}\n\n"

            "Belum ada budget "
            "untuk bulan ini."

        )

        keyboard = [

            [

                InlineKeyboardButton(

                    "➕ Set Budget",

                    callback_data=(
                        "budget_set"
                    ),

                ),

            ],

        ]

    # --------------------------------------------------------
    # SUDAH ADA
    # --------------------------------------------------------

    else:

        expense_total = (
            get_current_expense_total(
                user_id
            )
        )

        message = build_budget_message(

            budget,

            expense_total,

        )

        keyboard = [

            [

                InlineKeyboardButton(

                    "✏️ Ubah Budget",

                    callback_data=(
                        "budget_edit"
                    ),

                ),

            ],

        ]

    markup = InlineKeyboardMarkup(
        keyboard
    )

    # --------------------------------------------------------
    # CALLBACK
    # --------------------------------------------------------

    if update.callback_query:

        await update.callback_query.edit_message_text(

            message,

            reply_markup=markup,

            parse_mode="Markdown",

        )

    # --------------------------------------------------------
    # MESSAGE
    # --------------------------------------------------------

    elif update.message:

        await update.message.reply_text(

            message,

            reply_markup=markup,

            parse_mode="Markdown",

        )


# ============================================================
# /BUDGET
# ============================================================

async def budget_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await show_budget(
        update,
        context,
    )


# ============================================================
# SET BUDGET PROMPT
# ============================================================

async def set_budget_prompt(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:

        return

    await query.answer()

    context.user_data[
        "budget_input_mode"
    ] = True

    await query.edit_message_text(

        "💰 *Set Budget Bulanan*\n\n"

        "Masukkan nominal budget "
        "untuk bulan ini.\n\n"

        "Contoh:\n"
        "`2500000`\n"
        "`2.500.000`\n\n"

        "Kirim nominal sekarang.",

        parse_mode="Markdown",

    )


# ============================================================
# EDIT BUDGET PROMPT
# ============================================================

async def edit_budget_prompt(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:

        return

    await query.answer()

    context.user_data[
        "budget_input_mode"
    ] = True

    await query.edit_message_text(

        "✏️ *Ubah Budget Bulanan*\n\n"

        "Masukkan nominal budget "
        "baru untuk bulan ini.\n\n"

        "Contoh:\n"
        "`3000000`\n"
        "`3.000.000`",

        parse_mode="Markdown",

    )


# ============================================================
# HANDLE BUDGET INPUT
# ============================================================

async def budget_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:

        return False

    if not context.user_data.get(
        "budget_input_mode"
    ):

        return False

    value = (
        update.message.text.strip()
    )

    clean_value = (

        value

        .replace(
            "Rp",
            "",
        )

        .replace(
            "rp",
            "",
        )

        .replace(
            ".",
            "",
        )

        .replace(
            ",",
            "",
        )

        .strip()

    )

    if not clean_value.isdigit():

        await update.message.reply_text(

            "❌ Nominal tidak valid.\n\n"

            "Contoh:\n"
            "`2500000`\n"
            "`2.500.000`",

            parse_mode="Markdown",

        )

        return True

    amount = int(
        clean_value
    )

    if amount <= 0:

        await update.message.reply_text(

            "❌ Budget harus lebih dari "
            "Rp0."

        )

        return True

    if not update.effective_user:

        return True

    user_id = (
        update.effective_user.id
    )

    today = date.today()

    db = SessionLocal()

    try:

        statement = (
            select(Budget)
            .where(
                Budget.user_id == user_id,
                Budget.year == today.year,
                Budget.month == today.month,
            )
        )

        budget = db.scalar(
            statement
        )

        if budget is None:

            budget = Budget(

                user_id=user_id,

                year=today.year,

                month=today.month,

                amount=amount,

            )

            db.add(
                budget
            )

            action = "ditambahkan"

        else:

            budget.amount = amount

            action = "diperbarui"

        db.commit()

        context.user_data.pop(
            "budget_input_mode",
            None,
        )

        await update.message.reply_text(

            "✅ *Budget berhasil "
            f"{action}!*\n\n"

            f"💰 Budget "
            f"{get_month_name(today.month)} "
            f"{today.year}:\n\n"

            f"*{format_rupiah(amount)}*",

            parse_mode="Markdown",

        )

    except Exception as error:

        db.rollback()

        print(
            "Budget error:"
        )

        print(
            repr(error)
        )

        await update.message.reply_text(

            "❌ Terjadi kesalahan "
            "saat menyimpan budget."

        )

    finally:

        db.close()

    return True


# ============================================================
# CALLBACK HANDLERS
# ============================================================

budget_set_handler = (
    CallbackQueryHandler(

        set_budget_prompt,

        pattern=r"^budget_set$",

    )
)


budget_edit_handler = (
    CallbackQueryHandler(

        edit_budget_prompt,

        pattern=r"^budget_edit$",

    )
)