import os
import re

import pytesseract

from PIL import Image

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
# TESSERACT
# ============================================================

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


# ============================================================
# FORMAT RUPIAH
# ============================================================

def format_rupiah(
    amount: int,
) -> str:

    return f"Rp{amount:,}".replace(
        ",",
        ".",
    )


# ============================================================
# EXTRACT TOTAL
# ============================================================

def extract_total(
    text: str,
):
    """
    Mencari total pembayaran dari OCR.

    Contoh:

    Rp 28.000
    Rp28.000
    TOTAL 28.000
    TOTAL: Rp28.000
    GRAND TOTAL 28.000
    """

    patterns = [

        # TOTAL / GRAND TOTAL
        r"(?:grand\s+total|total|jumlah|bayar|amount)"
        r"\s*:?\s*(?:rp|idr)?\s*"
        r"([\d.,]+)",

        # RP NOMINAL
        r"\brp\s*([\d.,]+)",

    ]

    amounts = []

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE,
        )

        for value in matches:

            value = value.strip()

            # Hilangkan titik/koma pemisah
            normalized = re.sub(
                r"[.,]",
                "",
                value,
            )

            try:

                amount = int(
                    normalized
                )

                if amount > 0:
                    amounts.append(
                        amount
                    )

            except ValueError:

                continue

    if not amounts:
        return None

    # Ambil nominal terbesar
    return max(amounts)


# ============================================================
# EXTRACT MERCHANT
# ============================================================

def extract_merchant(
    text: str,
):
    """
    Mengambil kandidat nama merchant
    dari hasil OCR.
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    ignored_keywords = [
        "pembayaran",
        "berhasil",
        "lihat",
        "resi",
        "jakarta",
        "bagikan",
        "bayar",
        "sekarang",
        "dalam genggaman",
        "total",
        "jumlah",
        "grand total",
        "rp ",
    ]

    for line in lines:

        lower_line = line.lower()

        # Abaikan baris tertentu
        if any(
            keyword in lower_line
            for keyword in ignored_keywords
        ):
            continue

        # Abaikan baris yang hanya angka
        if re.fullmatch(
            r"[\d\s.,:/\-]+",
            line,
        ):
            continue

        # Abaikan baris terlalu pendek
        if len(line) < 4:
            continue

        # Merchant biasanya berupa teks
        return line

    return "Tidak diketahui"


# ============================================================
# EXTRACT DATE
# ============================================================

def extract_date(
    text: str,
):
    """
    Mendukung:

    27/08/2026
    27-08-2026
    27.08.2026
    27/08/26
    """

    pattern = (
        r"\b"
        r"(\d{1,2})"
        r"[\/\-.]"
        r"(\d{1,2})"
        r"[\/\-.]"
        r"(\d{2,4})"
        r"\b"
    )

    match = re.search(
        pattern,
        text,
    )

    if not match:
        return None

    day = match.group(1)

    month = match.group(2)

    year = match.group(3)

    if len(year) == 2:
        year = "20" + year

    return (
        f"{day.zfill(2)}/"
        f"{month.zfill(2)}/"
        f"{year}"
    )


# ============================================================
# DETECT CATEGORY
# ============================================================

def detect_category(
    text: str,
) -> str:

    text = text.lower()

    food_keywords = [
        "restaurant",
        "restoran",
        "cafe",
        "coffee",
        "kopi",
        "makan",
        "food",
        "warung",
        "bakso",
        "mie",
        "ayam",
    ]

    transport_keywords = [
        "bensin",
        "pertalite",
        "pertamax",
        "shell",
        "parking",
        "parkir",
        "grab",
        "gojek",
        "taxi",
        "tol",
    ]

    shopping_keywords = [
        "indomaret",
        "alfamart",
        "supermarket",
        "minimarket",
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


# ============================================================
# PROCESS RECEIPT
# ============================================================

def process_receipt(
    image_path: str,
):
    """
    Membaca foto menggunakan Tesseract
    dan mengembalikan hasil ekstraksi.
    """

    image = Image.open(
        image_path
    )

    text = pytesseract.image_to_string(
        image,
        lang="eng",
    )

    total = extract_total(
        text
    )

    merchant = extract_merchant(
        text
    )

    date = extract_date(
        text
    )

    category = detect_category(
        text
    )

    return {

        "raw_text": text,

        "merchant": merchant,

        "date": date,

        "total": total,

        "category": category,

    }


# ============================================================
# PHOTO HANDLER
# ============================================================

async def receipt_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:
        return

    if not update.message.photo:
        return

    user_id = update.effective_user.id

    # ==========================================
    # AMBIL FOTO TERBESAR
    # ==========================================

    photo = update.message.photo[-1]

    telegram_file = (
        await context.bot.get_file(
            photo.file_id
        )
    )

    # ==========================================
    # PATH FILE
    # ==========================================

    file_path = (
        f"temp_receipt_{user_id}.jpg"
    )

    # ==========================================
    # DOWNLOAD
    # ==========================================

    await telegram_file.download_to_drive(
        file_path
    )

    await update.message.reply_text(
        "🔎 Sedang membaca struk..."
    )

    try:

        # ======================================
        # OCR + EXTRACTION
        # ======================================

        result = process_receipt(
            file_path
        )

        merchant = result[
            "merchant"
        ]

        date = result[
            "date"
        ]

        total = result[
            "total"
        ]

        category = result[
            "category"
        ]

        # ======================================
        # DEBUG
        # ======================================

        print(
            "\n========== OCR =========="
        )

        print(
            result["raw_text"]
        )

        print(
            "==========================\n"
        )

        print(
            f"Merchant : {merchant}"
        )

        print(
            f"Date     : {date}"
        )

        print(
            f"Total    : {total}"
        )

        print(
            f"Category : {category}"
        )

        # ======================================
        # TOTAL TIDAK DITEMUKAN
        # ======================================

        if total is None:

            await update.message.reply_text(

                "❌ Saya belum bisa menemukan "
                "total pembayaran dari struk ini.\n\n"

                "Pastikan bagian total terlihat "
                "jelas pada foto."

            )

            return

        # ======================================
        # SIMPAN PENDING
        # ======================================

        context.user_data[
            "pending_receipt"
        ] = {

            "user_id": user_id,

            "merchant": merchant,

            "date": date,

            "amount": total,

            "category": category,

            "image_path": file_path,

            "raw_text": result[
                "raw_text"
            ],

        }

        # ======================================
        # DATE DISPLAY
        # ======================================

        date_text = (
            date
            if date
            else "Tidak terdeteksi"
        )

        # ======================================
        # CONFIRMATION
        # ======================================

        message = (

            "🧾 *Struk berhasil dibaca!*\n\n"

            f"🏪 Toko: {merchant}\n"

            f"📅 Tanggal: {date_text}\n"

            f"💰 Total: "
            f"{format_rupiah(total)}\n"

            f"🏷️ Kategori: {category}\n\n"

            "Apakah data ini sudah benar?"

        )

        keyboard = [

            [

                InlineKeyboardButton(
                    "✅ Simpan",
                    callback_data=(
                        "receipt_save"
                    ),
                ),

                InlineKeyboardButton(
                    "❌ Batal",
                    callback_data=(
                        "receipt_cancel"
                    ),
                ),

            ]

        ]

        reply_markup = (
            InlineKeyboardMarkup(
                keyboard
            )
        )

        await update.message.reply_text(

            message,

            reply_markup=reply_markup,

            parse_mode="Markdown",

        )

    except Exception as error:

        print(
            f"Receipt OCR error: {error}"
        )

        await update.message.reply_text(

            "❌ Terjadi kesalahan "
            "saat membaca struk."

        )


# ============================================================
# RECEIPT CALLBACK
# ============================================================

async def receipt_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    pending = context.user_data.get(
        "pending_receipt"
    )

    # ==========================================
    # BATAL
    # ==========================================

    if query.data == "receipt_cancel":

        image_path = None

        if pending:
            image_path = pending.get(
                "image_path"
            )

        context.user_data.pop(
            "pending_receipt",
            None,
        )

        # Hapus foto sementara
        if image_path and os.path.exists(
            image_path
        ):

            try:
                os.remove(
                    image_path
                )
            except OSError:
                pass

        await query.edit_message_text(
            "❌ Penyimpanan struk dibatalkan."
        )

        return

    # ==========================================
    # SIMPAN
    # ==========================================

    if query.data == "receipt_save":

        if not pending:

            await query.edit_message_text(

                "❌ Data struk "
                "sudah tidak tersedia."

            )

            return

        db = SessionLocal()

        try:

            # ==================================
            # BUAT EXPENSE
            # ==================================

            expense = Expense(

                user_id=pending[
                    "user_id"
                ],

                description=pending[
                    "merchant"
                ],

                amount=pending[
                    "amount"
                ],

                category=pending[
                    "category"
                ],

            )

            db.add(
                expense
            )

            db.commit()

            db.refresh(
                expense
            )

            image_path = pending.get(
                "image_path"
            )

            # ==================================
            # HAPUS FOTO SEMENTARA
            # ==================================

            if image_path and os.path.exists(
                image_path
            ):

                try:

                    os.remove(
                        image_path
                    )

                except OSError:

                    pass

            # ==================================
            # RESPONSE
            # ==================================

            await query.edit_message_text(

                "✅ *Struk berhasil disimpan!*\n\n"

                f"🏪 Toko: "
                f"{expense.description}\n"

                f"💰 Total: "
                f"{format_rupiah(expense.amount)}\n"

                f"🏷️ Kategori: "
                f"{expense.category}\n\n"

                "💾 Transaksi sudah masuk "
                "ke database.",

                parse_mode="Markdown",

            )

            context.user_data.pop(
                "pending_receipt",
                None,
            )

        except Exception as error:

            print(
                f"Receipt save error: {error}"
            )

            db.rollback()

            await query.edit_message_text(

                "❌ Terjadi kesalahan "
                "saat menyimpan struk."

            )

        finally:

            db.close()


# ============================================================
# CALLBACK HANDLER
# ============================================================

receipt_callback_handler = (
    CallbackQueryHandler(

        receipt_callback,

        pattern=(
            r"^receipt_(save|cancel)$"
        ),

    )
)