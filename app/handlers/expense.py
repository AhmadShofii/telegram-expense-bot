import re
from datetime import date

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
# FORMAT RUPIAH
# ============================================================

def format_rupiah(amount: int) -> str:

    return (
        f"Rp{int(amount):,}"
        .replace(",", ".")
    )


# ============================================================
# PARSE EXPENSE
# ============================================================

def parse_expense(text: str):

    """
    Format yang didukung:

    Makan siang 25000
    Makan siang 25.000
    Makan siang 25,000
    Bensin 50 ribu
    Bensin 50 rb
    """

    text = text.strip()

    if not text:
        return None

    # ========================================================
    # FORMAT RIBU / RB
    # ========================================================

    match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*(ribu|rb)\s*$",
        text,
        re.IGNORECASE,
    )

    if match:

        number = (
            match.group(1)
            .replace(",", ".")
        )

        try:

            amount = int(
                float(number) * 1000
            )

        except ValueError:

            return None

        description = (

            text[:match.start()]
            + text[match.end():]

        ).strip()

        if not description:

            return None

        return (
            description,
            amount,
        )

    # ========================================================
    # FORMAT ANGKA
    # ========================================================

    match = re.search(
        r"(\d[\d.,]*)$",
        text,
    )

    if not match:

        return None

    raw_amount = match.group(1)

    raw_amount = re.sub(
        r"[.,]",
        "",
        raw_amount,
    )

    try:

        amount = int(
            raw_amount
        )

    except ValueError:

        return None

    if amount <= 0:

        return None

    description = (
        text[:match.start()]
        .strip()
    )

    if not description:

        return None

    return (
        description,
        amount,
    )


# ============================================================
# DETECT CATEGORY
# ============================================================

def detect_category(
    description: str,
) -> str:

    text = description.lower()

    food_keywords = [

        "makan",
        "minum",
        "warteg",
        "restoran",
        "restaurant",
        "cafe",
        "kopi",
        "coffee",
        "nasi",
        "ayam",
        "bakso",
        "mie",
        "food",

    ]

    transport_keywords = [

        "bensin",
        "pertalite",
        "pertamax",
        "shell",
        "grab",
        "gojek",
        "ojek",
        "taxi",
        "tol",
        "parkir",
        "parking",

    ]

    shopping_keywords = [

        "belanja",
        "supermarket",
        "indomaret",
        "alfamart",
        "shopee",
        "tokopedia",
        "minimarket",

    ]

    health_keywords = [

        "obat",
        "apotek",
        "dokter",
        "rumah sakit",
        "rs",
        "vitamin",
        "kesehatan",

    ]

    entertainment_keywords = [

        "bioskop",
        "film",
        "game",
        "gaming",
        "steam",
        "netflix",
        "spotify",
        "hiburan",

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

    if any(
        keyword in text
        for keyword in health_keywords
    ):

        return "Kesehatan"

    if any(
        keyword in text
        for keyword in entertainment_keywords
    ):

        return "Hiburan"

    return "Lainnya"


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
# BUILD CONFIRMATION MESSAGE
# ============================================================

def build_confirmation_message(
    description: str,
    amount: int,
    category: str,
    expense_date: date,
) -> str:

    icon = category_icon(
        category
    )

    return (

        "🧾 *KONFIRMASI PENGELUARAN*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "📝 *Deskripsi*\n"
        f"{description}\n\n"

        "💵 *Nominal*\n"
        f"*{format_rupiah(amount)}*\n\n"

        f"{icon} *Kategori*\n"
        f"{category}\n\n"

        "📅 *Tanggal*\n"
        f"{expense_date.strftime('%d-%m-%Y')}\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "Pastikan data di atas sudah benar.\n"
        "Simpan transaksi sekarang?"

    )


# ============================================================
# INPUT MANUAL
# ============================================================

async def expense_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:

        return

    if not update.message.text:

        return

    result = parse_expense(
        update.message.text
    )

    # ========================================================
    # INVALID FORMAT
    # ========================================================

    if not result:

        await update.message.reply_text(

            "❌ *FORMAT TIDAK DIKENALI*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"

            "Gunakan format:\n\n"

            "📝 *Deskripsi + nominal*\n\n"

            "Contoh:\n"
            "• `Makan siang 25000`\n"
            "• `Bensin 50 ribu`\n"
            "• `Kopi 15000`\n"
            "• `Belanja 125.000`\n\n"

            "💡 Nominal bisa menggunakan "
            "`rb`, `ribu`, titik, atau angka biasa.",

            parse_mode="Markdown",

        )

        return

    description, amount = result

    category = detect_category(
        description
    )

    user_id = (
        update.effective_user.id
    )

    expense_date = date.today()

    # ========================================================
    # SIMPAN SEMENTARA
    # ========================================================

    context.user_data[
        "pending_expense"
    ] = {

        "user_id": user_id,

        "description": description,

        "amount": amount,

        "category": category,

        "expense_date": expense_date,

    }

    # ========================================================
    # BUTTON
    # ========================================================

    keyboard = [

        [

            InlineKeyboardButton(

                "✅ Simpan",

                callback_data=(
                    "expense_save"
                ),

            ),

            InlineKeyboardButton(

                "❌ Batal",

                callback_data=(
                    "expense_cancel"
                ),

            ),

        ],

    ]

    reply_markup = (
        InlineKeyboardMarkup(
            keyboard
        )
    )

    # ========================================================
    # CONFIRMATION
    # ========================================================

    message = build_confirmation_message(

        description,

        amount,

        category,

        expense_date,

    )

    await update.message.reply_text(

        message,

        reply_markup=reply_markup,

        parse_mode="Markdown",

    )


# ============================================================
# CALLBACK
# ============================================================

async def expense_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:

        return

    await query.answer()

    pending = (
        context.user_data.get(
            "pending_expense"
        )
    )

    # ========================================================
    # BATAL
    # ========================================================

    if query.data == "expense_cancel":

        context.user_data.pop(

            "pending_expense",

            None,

        )

        await query.edit_message_text(

            "❌ *PENCATATAN DIBATALKAN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"

            "Transaksi tidak disimpan.\n\n"

            "💡 Kamu bisa mencatat "
            "pengeluaran lagi kapan saja.",

            parse_mode="Markdown",

        )

        return

    # ========================================================
    # SIMPAN
    # ========================================================

    if query.data == "expense_save":

        if not pending:

            await query.edit_message_text(

                "❌ *DATA TIDAK DITEMUKAN*\n\n"

                "Data pengeluaran sudah "
                "tidak tersedia.\n\n"

                "Silakan masukkan transaksi "
                "kembali.",

                parse_mode="Markdown",

            )

            return

        db = SessionLocal()

        try:

            expense = Expense(

                user_id=pending[
                    "user_id"
                ],

                description=pending[
                    "description"
                ],

                amount=pending[
                    "amount"
                ],

                category=pending[
                    "category"
                ],

                expense_date=pending[
                    "expense_date"
                ],

            )

            db.add(
                expense
            )

            db.commit()

            db.refresh(
                expense
            )

            icon = category_icon(
                expense.category
            )

            await query.edit_message_text(

                "✅ *PENGELUARAN TERSIMPAN*\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"

                "🎉 Transaksi berhasil "
                "ditambahkan.\n\n"

                f"📝 *{expense.description}*\n"

                f"💵 *"
                f"{format_rupiah(expense.amount)}"
                f"*\n"

                f"{icon} "
                f"{expense.category}\n"

                f"📅 "
                f"{expense.expense_date.strftime('%d-%m-%Y')}\n\n"

                "━━━━━━━━━━━━━━━━━━━━\n\n"

                "📋 Transaksi sudah masuk "
                "ke riwayat pengeluaran."

                "\n\n"
                "Gunakan `/riwayat` "
                "untuk melihatnya.",

                parse_mode="Markdown",

            )

        except Exception as error:

            print(
                "❌ Expense save error:"
            )

            print(
                repr(error)
            )

            db.rollback()

            await query.edit_message_text(

                "❌ *GAGAL MENYIMPAN*\n\n"

                "Terjadi kesalahan saat "
                "menyimpan pengeluaran.\n\n"

                "Silakan coba lagi.",

                parse_mode="Markdown",

            )

        finally:

            db.close()

            context.user_data.pop(

                "pending_expense",

                None,

            )


# ============================================================
# CALLBACK HANDLER
# ============================================================

expense_callback_handler = (
    CallbackQueryHandler(

        expense_callback,

        pattern=(
            r"^expense_"
            r"(save|cancel)$"
        ),

    )
)