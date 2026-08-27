import csv
import os
import tempfile
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
# GET MONTHLY EXPENSES
# ============================================================

def get_monthly_expenses(
    user_id: int,
):

    start_date, end_date = (
        get_current_month_range()
    )

    db = SessionLocal()

    try:

        statement = (
            select(Expense)
            .where(
                Expense.user_id == user_id,
                Expense.expense_date >= start_date,
                Expense.expense_date < end_date,
            )
            .order_by(
                Expense.expense_date.asc(),
                Expense.id.asc(),
            )
        )

        expenses = db.scalars(
            statement
        ).all()

        # ====================================================
        # LOAD ITEMS
        # ====================================================

        for expense in expenses:

            try:

                list(
                    expense.items
                )

            except Exception:

                pass

        return expenses

    finally:

        db.close()


# ============================================================
# FORMAT AMOUNT
# ============================================================

def format_amount(
    amount,
) -> int:

    if amount is None:

        return 0

    return int(
        amount
    )


# ============================================================
# CREATE CSV
# ============================================================

def create_csv_file(
    user_id: int,
):

    expenses = get_monthly_expenses(
        user_id
    )

    if not expenses:

        return None

    today = date.today()

    month_name = MONTH_NAMES[
        today.month - 1
    ]

    # ========================================================
    # TEMP FILE
    # ========================================================

    temp_file = tempfile.NamedTemporaryFile(

        mode="w",

        suffix=".csv",

        prefix="expense_",

        delete=False,

        newline="",

        encoding="utf-8-sig",

    )

    file_path = (
        temp_file.name
    )

    try:

        writer = csv.writer(
            temp_file
        )

        # ====================================================
        # TITLE
        # ====================================================

        writer.writerow(
            [
                "Laporan Pengeluaran"
            ]
        )

        writer.writerow(
            [
                f"{month_name} {today.year}"
            ]
        )

        writer.writerow([])

        # ====================================================
        # HEADER
        # ====================================================

        writer.writerow(
            [
                "No",
                "Tanggal",
                "Deskripsi",
                "Kategori",
                "Nominal",
                "Item",
            ]
        )

        # ====================================================
        # DATA
        # ====================================================

        total = 0

        for index, expense in enumerate(

            expenses,

            start=1,

        ):

            amount = format_amount(
                expense.amount
            )

            total += amount

            # ================================================
            # ITEMS
            # ================================================

            item_text = ""

            try:

                items = list(
                    expense.items
                )

            except Exception:

                items = []

            if items:

                item_parts = []

                for item in items:

                    item_name = (

                        getattr(
                            item,
                            "name",
                            "",
                        )

                        or ""

                    )

                    quantity = getattr(

                        item,

                        "quantity",

                        1,

                    )

                    item_amount = getattr(

                        item,

                        "amount",

                        0,

                    )

                    if (

                        quantity

                        and quantity != 1

                    ):

                        item_parts.append(

                            f"{item_name} "
                            f"x{quantity} "
                            f"{format_rupiah(item_amount)}"

                        )

                    else:

                        item_parts.append(

                            f"{item_name} "
                            f"{format_rupiah(item_amount)}"

                        )

                item_text = (
                    " | ".join(
                        item_parts
                    )
                )

            # ================================================
            # DATE
            # ================================================

            expense_date = (
                expense.expense_date
            )

            if expense_date:

                date_text = (
                    expense_date.strftime(
                        "%d-%m-%Y"
                    )
                )

            else:

                date_text = ""

            # ================================================
            # ROW
            # ================================================

            writer.writerow(

                [

                    index,

                    date_text,

                    expense.description
                    or "",

                    expense.category
                    or "Lainnya",

                    amount,

                    item_text,

                ]

            )

        # ====================================================
        # TOTAL
        # ====================================================

        writer.writerow([])

        writer.writerow(

            [

                "",

                "",

                "",

                "TOTAL",

                total,

                "",

            ]

        )

        temp_file.flush()

    finally:

        temp_file.close()

    return file_path


# ============================================================
# GET EXPORT SUMMARY
# ============================================================

def get_export_summary(
    expenses,
):

    total = sum(

        format_amount(
            expense.amount
        )

        for expense in expenses

    )

    transaction_count = len(
        expenses
    )

    category_count = len({

        expense.category
        or "Lainnya"

        for expense in expenses

    })

    return (

        total,

        transaction_count,

        category_count,

    )


# ============================================================
# /EXPORT
# ============================================================

async def export_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.effective_user:

        return

    user_id = (
        update.effective_user.id
    )

    processing_message = None

    file_path = None

    try:

        # ====================================================
        # PROCESSING MESSAGE
        # ====================================================

        if update.message:

            processing_message = (

                await update.message.reply_text(

                    "📤 *MENYIAPKAN EXPORT*\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"

                    "⏳ Sedang membuat "
                    "laporan pengeluaran...\n\n"

                    "Mohon tunggu sebentar.",

                    parse_mode="Markdown",

                )

            )

        # ====================================================
        # GET EXPENSES
        # ====================================================

        expenses = get_monthly_expenses(
            user_id
        )

        # ====================================================
        # NO DATA
        # ========================================================

        if not expenses:

            if processing_message:

                await processing_message.edit_text(

                    "📤 *EXPORT LAPORAN*\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"

                    "📭 *Belum ada data*\n\n"

                    "Belum ada pengeluaran "
                    "pada bulan ini.\n\n"

                    "Catat transaksi terlebih "
                    "dahulu sebelum melakukan "
                    "export.",

                    parse_mode="Markdown",

                )

            return

        # ====================================================
        # CREATE FILE
        # ====================================================

        file_path = create_csv_file(
            user_id
        )

        if not file_path:

            raise RuntimeError(
                "CSV file gagal dibuat."
            )

        # ====================================================
        # SUMMARY
        # ====================================================

        total, transaction_count, category_count = (

            get_export_summary(
                expenses
            )

        )

        today = date.today()

        month_name = MONTH_NAMES[
            today.month - 1
        ]

        # ====================================================
        # DELETE PROCESSING
        # ====================================================

        if processing_message:

            try:

                await processing_message.delete()

            except Exception:

                pass

        # ====================================================
        # SEND FILE
        # ====================================================

        with open(

            file_path,

            "rb",

        ) as csv_file:

            if update.message:

                await update.message.reply_document(

                    document=csv_file,

                    filename=(

                        f"laporan_pengeluaran_"

                        f"{today.year}_"

                        f"{today.month:02d}.csv"

                    ),

                    caption=(

                        "📤 *EXPORT BERHASIL*\n"
                        "━━━━━━━━━━━━━━━━━━━━\n\n"

                        f"🗓️ *{month_name} "
                        f"{today.year}*\n\n"

                        "📊 *Ringkasan*\n\n"

                        f"🧾 Transaksi: "
                        f"*{transaction_count}*\n"

                        f"🏷️ Kategori: "
                        f"*{category_count}*\n"

                        f"💸 Total: "
                        f"*{format_rupiah(total)}*\n\n"

                        "📄 Format: *CSV*\n\n"

                        "File dapat dibuka dengan "
                        "Microsoft Excel, "
                        "Google Sheets, atau "
                        "aplikasi spreadsheet lainnya."

                    ),

                    parse_mode="Markdown",

                )

        # ====================================================
        # CLEANUP
        # ====================================================

        try:

            if (

                file_path

                and os.path.exists(
                    file_path
                )

            ):

                os.remove(
                    file_path
                )

        except OSError:

            pass

        file_path = None

    except Exception as error:

        print(
            "❌ Export error:"
        )

        print(
            repr(error)
        )

        # ====================================================
        # ERROR MESSAGE
        # ====================================================

        if processing_message:

            try:

                await processing_message.edit_text(

                    "❌ *EXPORT GAGAL*\n"
                    "━━━━━━━━━━━━━━━━━━━━\n\n"

                    "Terjadi kesalahan saat "
                    "membuat laporan.\n\n"

                    "Silakan coba lagi.",

                    parse_mode="Markdown",

                )

            except Exception:

                pass

        elif update.message:

            await update.message.reply_text(

                "❌ *EXPORT GAGAL*\n\n"

                "Terjadi kesalahan saat "
                "membuat laporan.\n\n"

                "Silakan coba lagi.",

                parse_mode="Markdown",

            )

    finally:

        # ====================================================
        # FINAL CLEANUP
        # ====================================================

        try:

            if (

                file_path

                and os.path.exists(
                    file_path
                )

            ):

                os.remove(
                    file_path
                )

        except OSError:

            pass