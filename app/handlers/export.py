import csv
import os
import tempfile
from datetime import date

from sqlalchemy import select

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
# GET MONTH RANGE
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
# GET EXPENSES
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

                # Memaksa relationship items
                # untuk dibaca sebelum session ditutup.
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

                    if quantity and quantity != 1:

                        item_parts.append(

                            f"{item_name} "
                            f"x{quantity} "
                            f"Rp{format_amount(item_amount):,}"

                        )

                    else:

                        item_parts.append(

                            f"{item_name} "
                            f"Rp{format_amount(item_amount):,}"

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
                    expense.description or "",
                    expense.category or "Lainnya",
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

    try:

        # ====================================================
        # PROCESSING
        # ====================================================

        if update.message:

            processing_message = (
                await update.message.reply_text(
                    "📤 Sedang membuat "
                    "laporan..."
                )
            )

        # ====================================================
        # CREATE CSV
        # ========================================================

        file_path = create_csv_file(
            user_id
        )

        # ====================================================
        # NO DATA
        # ========================================================

        if not file_path:

            if processing_message:

                await processing_message.edit_text(

                    "📭 Belum ada "
                    "pengeluaran pada "
                    "bulan ini.\n\n"

                    "Belum ada laporan "
                    "yang dapat diekspor."

                )

            elif update.message:

                await update.message.reply_text(

                    "📭 Belum ada "
                    "pengeluaran pada "
                    "bulan ini."

                )

            return

        # ====================================================
        # MONTH
        # ====================================================

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

                        "📊 *Laporan Pengeluaran*\n\n"

                        f"🗓️ "
                        f"{month_name} "
                        f"{today.year}\n\n"

                        "File CSV berisi "
                        "seluruh pengeluaran "
                        "bulan berjalan."

                    ),

                    parse_mode="Markdown",

                )

        # ====================================================
        # DELETE TEMP FILE
        # ====================================================

        try:

            if os.path.exists(
                file_path
            ):

                os.remove(
                    file_path
                )

        except OSError:

            pass

    except Exception as error:

        print(
            "Export error:"
        )

        print(
            repr(error)
        )

        if processing_message:

            try:

                await processing_message.edit_text(

                    "❌ Terjadi kesalahan "
                    "saat membuat laporan."

                )

            except Exception:

                pass

        elif update.message:

            await update.message.reply_text(

                "❌ Terjadi kesalahan "
                "saat membuat laporan."

            )

        # ====================================================
        # CLEANUP
        # ====================================================

        try:

            if (
                "file_path" in locals()
                and file_path
                and os.path.exists(
                    file_path
                )
            ):

                os.remove(
                    file_path
                )

        except OSError:

            pass