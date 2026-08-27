import re

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


def parse_expense(text: str):
    """
    Format yang didukung:

    Makan siang 25000
    Makan siang 25.000
    Makan siang 25,000
    Bensin 25 ribu
    """

    text = text.strip()

    # Format: 25 ribu / 25 rb
    match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*(ribu|rb)",
        text,
        re.IGNORECASE,
    )

    if match:
        number = match.group(1).replace(",", ".")

        try:
            amount = int(float(number) * 1000)
        except ValueError:
            return None

        description = (
            text[:match.start()]
            + text[match.end():]
        ).strip()

        if not description:
            return None

        return description, amount

    # Format angka biasa di akhir kalimat
    match = re.search(
        r"(\d[\d.,]*)$",
        text,
    )

    if not match:
        return None

    raw_amount = match.group(1)

    # Hilangkan titik dan koma
    raw_amount = re.sub(
        r"[.,]",
        "",
        raw_amount,
    )

    try:
        amount = int(raw_amount)
    except ValueError:
        return None

    description = text[:match.start()].strip()

    if not description:
        return None

    return description, amount


def detect_category(description: str) -> str:
    """
    Menentukan kategori berdasarkan keyword sederhana.
    """

    text = description.lower()

    food_keywords = [
        "makan",
        "minum",
        "warteg",
        "restoran",
        "restaurant",
        "cafe",
        "kopi",
        "nasi",
        "ayam",
        "bakso",
        "mie",
    ]

    transport_keywords = [
        "bensin",
        "pertalite",
        "pertamax",
        "grab",
        "gojek",
        "ojek",
        "taxi",
        "tol",
        "parkir",
    ]

    shopping_keywords = [
        "belanja",
        "supermarket",
        "indomaret",
        "alfamart",
        "shopee",
        "tokopedia",
    ]

    if any(
        keyword in text
        for keyword in food_keywords
    ):
        return "Makanan"

    if any(
        keyword in text
        for keyword in transport_keywords
    ):
        return "Transportasi"

    if any(
        keyword in text
        for keyword in shopping_keywords
    ):
        return "Belanja"

    return "Lainnya"


def format_rupiah(amount: int) -> str:
    return f"Rp{amount:,}".replace(",", ".")


async def expense_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Menerima pesan seperti:

    Makan siang 25000
    Bensin 50 ribu
    Kopi 15000
    """

    if not update.message:
        return

    if not update.message.text:
        return

    result = parse_expense(
        update.message.text
    )

    if not result:
        await update.message.reply_text(
            "❌ Format pengeluaran belum dikenali.\n\n"
            "Contoh:\n"
            "• Makan siang 25000\n"
            "• Bensin 50 ribu\n"
            "• Kopi 15000"
        )
        return

    description, amount = result

    category = detect_category(
        description
    )

    user_id = update.effective_user.id

    # Simpan sementara sebelum konfirmasi
    context.user_data["pending_expense"] = {
        "user_id": user_id,
        "description": description,
        "amount": amount,
        "category": category,
    }

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Simpan",
                callback_data="expense_save",
            ),
            InlineKeyboardButton(
                "❌ Batal",
                callback_data="expense_cancel",
            ),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )

    await update.message.reply_text(
        "💰 *Pengeluaran ditemukan*\n\n"
        f"📝 Deskripsi: {description}\n"
        f"💵 Nominal: {format_rupiah(amount)}\n"
        f"🏷️ Kategori: {category}\n\n"
        "Apakah ingin menyimpan transaksi ini?",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def expense_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Menangani tombol Simpan / Batal.
    """

    query = update.callback_query

    if not query:
        return

    await query.answer()

    pending = context.user_data.get(
        "pending_expense"
    )

    # Batal
    if query.data == "expense_cancel":

        context.user_data.pop(
            "pending_expense",
            None,
        )

        await query.edit_message_text(
            "❌ Pengeluaran dibatalkan."
        )

        return

    # Simpan
    if query.data == "expense_save":

        if not pending:
            await query.edit_message_text(
                "❌ Data pengeluaran sudah tidak tersedia."
            )
            return

        db = SessionLocal()

        try:
            expense = Expense(
                user_id=pending["user_id"],
                description=pending["description"],
                amount=pending["amount"],
                category=pending["category"],
            )

            db.add(expense)
            db.commit()
            db.refresh(expense)

            await query.edit_message_text(
                "✅ *Pengeluaran berhasil disimpan!*\n\n"
                f"📝 {expense.description}\n"
                f"💵 {format_rupiah(expense.amount)}\n"
                f"🏷️ {expense.category}",
                parse_mode="Markdown",
            )

        except Exception:
            db.rollback()

            await query.edit_message_text(
                "❌ Terjadi kesalahan saat menyimpan "
                "pengeluaran."
            )

        finally:
            db.close()

            context.user_data.pop(
                "pending_expense",
                None,
            )


expense_callback_handler = CallbackQueryHandler(
    expense_callback,
    pattern=r"^expense_(save|cancel)$",
)