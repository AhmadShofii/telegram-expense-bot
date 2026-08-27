from datetime import date

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import ContextTypes

from database.db import SessionLocal
from database.models import Expense, Budget


# ============================================================
# FORMAT RUPIAH
# ============================================================

def format_rupiah(amount: int) -> str:
    return f"Rp{amount:,}".replace(",", ".")


# ============================================================
# MAIN MENU KEYBOARD
# ============================================================

def build_main_keyboard():

    keyboard = [

        [
            InlineKeyboardButton(
                "📝 Catat Pengeluaran",
                callback_data="start_expense",
            ),
        ],

        [
            InlineKeyboardButton(
                "📷 Scan Struk",
                callback_data="start_receipt",
            ),

            InlineKeyboardButton(
                "📋 Riwayat",
                callback_data="start_history",
            ),
        ],

        [
            InlineKeyboardButton(
                "💰 Budget",
                callback_data="start_budget",
            ),

            InlineKeyboardButton(
                "📊 Statistik",
                callback_data="start_statistics",
            ),
        ],

        [
            InlineKeyboardButton(
                "📈 Laporan",
                callback_data="start_report",
            ),

            InlineKeyboardButton(
                "📤 Export",
                callback_data="start_export",
            ),
        ],

        [
            InlineKeyboardButton(
                "🔔 Daily Reminder",
                callback_data="start_reminder",
            ),
        ],

        [
            InlineKeyboardButton(
                "❓ Bantuan",
                callback_data="start_help",
            ),
        ],

    ]

    return InlineKeyboardMarkup(keyboard)


# ============================================================
# GET TODAY SUMMARY
# ============================================================

def get_today_summary(user_id: int):

    db = SessionLocal()

    try:

        today = date.today()

        expenses = (

            db.query(Expense)

            .filter(
                Expense.user_id == user_id,
                Expense.expense_date == today,
            )

            .all()

        )

        total = sum(
            expense.amount
            for expense in expenses
        )

        count = len(expenses)

        return total, count

    except Exception as error:

        print(
            "❌ Start summary error:"
        )

        print(
            repr(error)
        )

        return 0, 0

    finally:

        db.close()


# ============================================================
# GET MONTHLY BUDGET
# ============================================================

def get_monthly_budget(user_id: int):

    db = SessionLocal()

    try:

        today = date.today()

        budget = (

            db.query(Budget)

            .filter(

                Budget.user_id == user_id,

                Budget.year == today.year,

                Budget.month == today.month,

            )

            .first()

        )

        if budget is None:

            return None

        return budget.amount

    except Exception as error:

        print(
            "❌ Start budget error:"
        )

        print(
            repr(error)
        )

        return None

    finally:

        db.close()


# ============================================================
# GET MONTHLY EXPENSE
# ============================================================

def get_monthly_expense(user_id: int):

    db = SessionLocal()

    try:

        today = date.today()

        expenses = (

            db.query(Expense)

            .filter(

                Expense.user_id == user_id,

                Expense.expense_date >= date(
                    today.year,
                    today.month,
                    1,
                ),

                Expense.expense_date <= today,

            )

            .all()

        )

        return sum(
            expense.amount
            for expense in expenses
        )

    except Exception as error:

        print(
            "❌ Start monthly expense error:"
        )

        print(
            repr(error)
        )

        return 0

    finally:

        db.close()


# ============================================================
# PROGRESS BAR
# ============================================================

def build_progress_bar(
    used: int,
    budget: int,
    length: int = 10,
) -> str:

    if budget <= 0:

        return "░" * length

    percentage = (
        used / budget
    )

    percentage = max(
        0,
        min(
            percentage,
            1,
        ),
    )

    filled = int(
        percentage * length
    )

    empty = (
        length - filled
    )

    return (
        "█" * filled
        + "░" * empty
    )


# ============================================================
# DASHBOARD MESSAGE
# ============================================================

def build_dashboard(
    user_id: int,
    first_name: str,
):

    today_total, today_count = (
        get_today_summary(user_id)
    )

    budget = get_monthly_budget(
        user_id
    )

    monthly_used = get_monthly_expense(
        user_id
    )

    today = date.today()

    # ========================================================
    # BUDGET SECTION
    # ========================================================

    if budget is not None:

        remaining = (
            budget - monthly_used
        )

        if remaining < 0:

            remaining = 0

        percentage = (
            monthly_used / budget * 100
        )

        percentage = min(
            percentage,
            100,
        )

        progress = build_progress_bar(
            monthly_used,
            budget,
        )

        if monthly_used > budget:

            budget_status = (
                "🔴 Budget terlampaui"
            )

        elif monthly_used >= budget * 0.8:

            budget_status = (
                "🟡 Mendekati batas budget"
            )

        else:

            budget_status = (
                "🟢 Budget masih aman"
            )

        budget_section = (

            "💰 *BUDGET BULAN INI*\n\n"

            f"🎯 Budget: "
            f"{format_rupiah(budget)}\n"

            f"💸 Terpakai: "
            f"{format_rupiah(monthly_used)}\n"

            f"💵 Sisa: "
            f"{format_rupiah(remaining)}\n\n"

            f"{progress} "
            f"{percentage:.0f}%\n"

            f"{budget_status}"

        )

    else:

        budget_section = (

            "💰 *BUDGET BULAN INI*\n\n"

            "Belum ada budget yang ditetapkan.\n\n"

            "Gunakan /budget untuk "
            "mengatur budget bulanan."

        )

    # ========================================================
    # DASHBOARD
    # ========================================================

    message = (

        f"👋 *Halo, {first_name}!*\n\n"

        "💰 *EXPENSE BOT*\n"

        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "📊 *RINGKASAN HARI INI*\n\n"

        f"💸 Pengeluaran: "
        f"*{format_rupiah(today_total)}*\n"

        f"🧾 Transaksi: "
        f"*{today_count} transaksi*\n"

        f"📅 {today.strftime('%d %B %Y')}\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n\n"

        f"{budget_section}\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "✨ *Apa yang ingin kamu lakukan?*\n\n"

        "Pilih menu di bawah untuk mulai."

    )

    return message


# ============================================================
# START COMMAND
# ============================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:

        return

    user = update.effective_user

    if user is None:

        return

    first_name = (
        user.first_name
        or "Pengguna"
    )

    message = build_dashboard(

        user_id=user.id,

        first_name=first_name,

    )

    await update.message.reply_text(

        message,

        reply_markup=(
            build_main_keyboard()
        ),

        parse_mode="Markdown",

    )