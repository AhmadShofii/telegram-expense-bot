import os
import re
from datetime import datetime

import pytesseract

from PIL import (
    Image,
    ImageEnhance,
    ImageFilter,
    ImageOps,
)

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
from database.models import (
    Expense,
    ExpenseItem,
)


# ============================================================
# TESSERACT CONFIGURATION
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
# NORMALIZE AMOUNT
# ============================================================

def normalize_amount(
    value: str,
):
    """
    Mengubah nominal OCR menjadi integer.

    Contoh:

    28.000 -> 28000
    28,000 -> 28000
    28000  -> 28000
    """

    if not value:
        return None

    value = value.strip()

    value = re.sub(
        r"[^\d.,]",
        "",
        value,
    )

    if not value:
        return None

    # Format Indonesia:
    # 28.000
    # 1.250.000
    if "." in value:

        parts = value.split(".")

        if all(
            len(part) == 3
            for part in parts[1:]
        ):
            value = "".join(parts)

    # Format:
    # 28,000
    # 1,250,000
    elif "," in value:

        parts = value.split(",")

        if all(
            len(part) == 3
            for part in parts[1:]
        ):
            value = "".join(parts)

    value = re.sub(
        r"[.,]",
        "",
        value,
    )

    try:

        return int(value)

    except ValueError:

        return None


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def preprocess_image(
    image_path: str,
):
    """
    Preprocessing gambar sebelum OCR.
    """

    image = Image.open(
        image_path
    )

    # Grayscale
    image = ImageOps.grayscale(
        image
    )

    # Resize
    width, height = image.size

    image = image.resize(
        (
            width * 2,
            height * 2,
        )
    )

    # Contrast
    enhancer = ImageEnhance.Contrast(
        image
    )

    image = enhancer.enhance(
        2.0
    )

    # Sharpen
    image = image.filter(
        ImageFilter.SHARPEN
    )

    return image


# ============================================================
# OCR
# ============================================================

def perform_ocr(
    image_path: str,
):
    """
    Menjalankan OCR Tesseract.
    """

    image = preprocess_image(
        image_path
    )

    text = pytesseract.image_to_string(
        image,
        lang="eng",
        config="--psm 6",
    )

    return text


# ============================================================
# EXTRACT TOTAL
# ============================================================

def extract_total(
    text: str,
):
    """
    Mencari total pembayaran.

    Contoh:

    TOTAL 28.000
    TOTAL: Rp28.000
    GRAND TOTAL 28.000
    Nominal Transaksi
    Rp 8.000
    """

    amounts = []

    # ========================================================
    # PRIORITAS 1
    # TOTAL
    # ========================================================

    priority_patterns = [

        r"(?:grand\s*total)"
        r"\s*:?\s*"
        r"(?:rp|idr)?\s*"
        r"([\d.,]+)",

        r"(?:total)"
        r"\s*:?\s*"
        r"(?:rp|idr)?\s*"
        r"([\d.,]+)",

        r"(?:jumlah)"
        r"\s*:?\s*"
        r"(?:rp|idr)?\s*"
        r"([\d.,]+)",

        r"(?:nominal\s+transaksi)"
        r"\s*:?\s*"
        r"(?:rp|idr)?\s*"
        r"([\d.,]+)",

        r"(?:bayar)"
        r"\s*:?\s*"
        r"(?:rp|idr)?\s*"
        r"([\d.,]+)",
    ]

    for pattern in priority_patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE,
        )

        for value in matches:

            amount = normalize_amount(
                value
            )

            if amount and amount > 0:

                amounts.append(
                    amount
                )

    if amounts:

        return max(
            amounts
        )

    # ========================================================
    # PRIORITAS 2
    # NOMINAL RP
    # ========================================================

    rp_matches = re.findall(
        r"\b(?:rp|idr)\s*([\d.,]+)",
        text,
        re.IGNORECASE,
    )

    for value in rp_matches:

        amount = normalize_amount(
            value
        )

        if amount and amount > 0:

            amounts.append(
                amount
            )

    if amounts:

        return max(
            amounts
        )

    return None


# ============================================================
# VALIDATE MERCHANT
# ============================================================

def is_valid_merchant(
    value: str,
) -> bool:
    """
    Memastikan kandidat merchant valid.
    """

    if not value:

        return False

    value = value.strip()

    if len(value) < 3:

        return False

    # Harus mengandung huruf
    if not re.search(
        r"[A-Za-z]",
        value,
    ):

        return False

    # Jangan angka murni
    if re.fullmatch(
        r"[\d\s.,:/\-]+",
        value,
    ):

        return False

    # Jangan nominal
    if re.fullmatch(
        r"(rp|idr)?\s*[\d.,]+",
        value,
        re.IGNORECASE,
    ):

        return False

    # Noise OCR
    noise_chars = [
        "@",
        "%",
        "©",
        "®",
        "™",
    ]

    noise_count = sum(
        value.count(char)
        for char in noise_chars
    )

    if noise_count >= 1:

        return False

    return True


# ============================================================
# EXTRACT MERCHANT
# ============================================================

def extract_merchant(
    text: str,
):
    """
    Mencari merchant berdasarkan label.

    Contoh:

    Penerima
    PT Tokopedia

    atau:

    Merchant
    Starbucks
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    labels = [
        "penerima",
        "merchant",
        "toko",
        "store",
        "outlet",
        "recipient",
    ]

    # ========================================================
    # CARI BERDASARKAN LABEL
    # ========================================================

    for index, line in enumerate(
        lines
    ):

        normalized = (
            line.lower()
            .strip()
        )

        if normalized in labels:

            if index + 1 < len(lines):

                candidate = (
                    lines[index + 1]
                    .strip()
                )

                if is_valid_merchant(
                    candidate
                ):

                    return candidate

    # ========================================================
    # FALLBACK
    # ========================================================

    ignored_keywords = [

        "pembayaran",
        "berhasil",

        "lihat",
        "resi",

        "bagikan",

        "bayar",
        "sekarang",

        "dalam genggaman",

        "total",
        "jumlah",
        "grand total",

        "subtotal",
        "sub total",

        "nominal transaksi",

        "tanggal",
        "date",

        "waktu",
        "time",

        "jakarta",
        "indonesia",

        "rp",
        "idr",

    ]

    for line in lines[:15]:

        lower_line = (
            line.lower()
        )

        if any(
            keyword in lower_line
            for keyword in ignored_keywords
        ):

            continue

        if not re.search(
            r"[A-Za-z]",
            line,
        ):

            continue

        if re.search(
            r"\d{1,2}"
            r"\s+[A-Za-z]+"
            r"\s+\d{4}",
            line,
        ):

            continue

        if re.fullmatch(
            r"[\d\s.,:/\-]+",
            line,
        ):

            continue

        if not is_valid_merchant(
            line
        ):

            continue

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

    25/07/2026
    25-07-2026
    25.07.2026

    25 Jul 2026
    25 July 2026
    """

    # ========================================================
    # FORMAT ANGKA
    # ========================================================

    numeric_pattern = (
        r"\b"
        r"(\d{1,2})"
        r"[\/\-.]"
        r"(\d{1,2})"
        r"[\/\-.]"
        r"(\d{2,4})"
        r"\b"
    )

    match = re.search(
        numeric_pattern,
        text,
        re.IGNORECASE,
    )

    if match:

        day = int(
            match.group(1)
        )

        month = int(
            match.group(2)
        )

        year = int(
            match.group(3)
        )

        if year < 100:

            year += 2000

        try:

            return datetime(
                year,
                month,
                day,
            ).date()

        except ValueError:

            pass

    # ========================================================
    # FORMAT NAMA BULAN
    # ========================================================

    month_map = {

        "jan": 1,
        "januari": 1,
        "january": 1,

        "feb": 2,
        "februari": 2,
        "february": 2,

        "mar": 3,
        "maret": 3,
        "march": 3,

        "apr": 4,
        "april": 4,

        "mei": 5,
        "may": 5,

        "jun": 6,
        "juni": 6,
        "june": 6,

        "jul": 7,
        "juli": 7,
        "july": 7,

        "agu": 8,
        "agustus": 8,
        "aug": 8,
        "august": 8,

        "sep": 9,
        "september": 9,

        "okt": 10,
        "oktober": 10,
        "oct": 10,
        "october": 10,

        "nov": 11,
        "november": 11,

        "des": 12,
        "desember": 12,
        "dec": 12,
        "december": 12,

    }

    month_pattern = (
        r"\b"
        r"(\d{1,2})"
        r"\s+"
        r"([A-Za-z]+)"
        r"\s+"
        r"(\d{4})"
        r"\b"
    )

    match = re.search(
        month_pattern,
        text,
        re.IGNORECASE,
    )

    if not match:

        return None

    day = int(
        match.group(1)
    )

    month_name = (
        match.group(2)
        .lower()
    )

    year = int(
        match.group(3)
    )

    month = month_map.get(
        month_name
    )

    if month is None:

        return None

    try:

        return datetime(
            year,
            month,
            day,
        ).date()

    except ValueError:

        return None


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
        "nasi",
        "pizza",
        "burger",
        "kuliner",
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
        "fuel",
    ]

    shopping_keywords = [
        "indomaret",
        "alfamart",
        "supermarket",
        "minimarket",
        "shopee",
        "tokopedia",
        "mall",
        "store",
        "mart",
    ]

    health_keywords = [
        "apotek",
        "pharmacy",
        "rumah sakit",
        "hospital",
        "klinik",
        "clinic",
        "obat",
    ]

    entertainment_keywords = [
        "bioskop",
        "cinema",
        "netflix",
        "spotify",
        "game",
        "steam",
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
# EXTRACT ITEMS
# ============================================================

def extract_items(
    text: str,
    total: int | None = None,
):
    """
    Mencoba mengambil item dari struk.

    Contoh:

    NASI GORENG 20.000
    ES TEH 8.000
    TOTAL 28.000
    """

    items = []

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    ignored_keywords = [
        "total",
        "grand total",
        "jumlah",
        "subtotal",
        "sub total",
        "pajak",
        "tax",
        "service",
        "diskon",
        "discount",
        "kembalian",
        "cash",
        "tunai",
        "bayar",
        "pembayaran",
        "berhasil",
        "resi",
        "bagikan",
        "jakarta",
        "alamat",
        "tel",
        "phone",
        "tanggal",
        "waktu",
        "payment",
        "penerima",
        "nominal transaksi",
    ]

    amount_pattern = re.compile(
        r"^(.+?)"
        r"\s+"
        r"(?:Rp|IDR)?\s*"
        r"(\d[\d.,]*)"
        r"\s*$",
        re.IGNORECASE,
    )

    for line in lines:

        lower_line = (
            line.lower()
        )

        if any(
            keyword in lower_line
            for keyword in ignored_keywords
        ):

            continue

        match = amount_pattern.match(
            line
        )

        if not match:

            continue

        name = (
            match.group(1)
            .strip()
        )

        amount_text = (
            match.group(2)
        )

        name = re.sub(
            r"^[\s\-:|]+",
            "",
            name,
        )

        name = re.sub(
            r"[\s\-:|]+$",
            "",
            name,
        )

        if len(name) < 2:

            continue

        amount = normalize_amount(
            amount_text
        )

        if amount is None:

            continue

        if amount <= 0:

            continue

        # Jangan masukkan total sebagai item
        if (
            total is not None
            and amount == total
        ):

            continue

        quantity = 1

        quantity_match = re.search(
            r"(?:x|qty|quantity)"
            r"\s*(\d+)",
            name,
            re.IGNORECASE,
        )

        if quantity_match:

            quantity = int(
                quantity_match.group(1)
            )

            name = re.sub(
                r"(?:x|qty|quantity)"
                r"\s*\d+",
                "",
                name,
                flags=re.IGNORECASE,
            ).strip()

        items.append(
            {
                "name": name,
                "quantity": quantity,
                "amount": amount,
            }
        )

    return items


# ============================================================
# PROCESS RECEIPT
# ============================================================

def process_receipt(
    image_path: str,
):

    text = perform_ocr(
        image_path
    )

    total = extract_total(
        text
    )

    merchant = extract_merchant(
        text
    )

    expense_date = extract_date(
        text
    )

    category = detect_category(
        text
    )

    items = extract_items(
        text,
        total,
    )

    return {

        "raw_text": text,

        "merchant": merchant,

        "date": expense_date,

        "total": total,

        "category": category,

        "items": items,

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

    user = update.effective_user

    if not user:

        return

    user_id = user.id

    # ==========================================
    # FOTO TERBESAR
    # ==========================================

    photo = (
        update.message.photo[-1]
    )

    telegram_file = (
        await context.bot.get_file(
            photo.file_id
        )
    )

    # ==========================================
    # PATH
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

    processing_message = (
        await update.message.reply_text(
            "🔎 Sedang membaca struk..."
        )
    )

    try:

        result = process_receipt(
            file_path
        )

        merchant = result[
            "merchant"
        ]

        expense_date = result[
            "date"
        ]

        total = result[
            "total"
        ]

        category = result[
            "category"
        ]

        items = result[
            "items"
        ]

        # ======================================
        # DEBUG
        # ======================================

        print(
            "\n================================"
        )

        print(
            "OCR RESULT"
        )

        print(
            "================================"
        )

        print(
            result["raw_text"]
        )

        print(
            "================================"
        )

        print(
            f"Merchant : {merchant}"
        )

        print(
            f"Date     : {expense_date}"
        )

        print(
            f"Total    : {total}"
        )

        print(
            f"Category : {category}"
        )

        print(
            f"Items    : {items}"
        )

        print(
            "================================\n"
        )

        # ======================================
        # TOTAL TIDAK DITEMUKAN
        # ======================================

        if total is None:

            await processing_message.edit_text(

                "❌ Saya belum bisa menemukan "
                "total pembayaran dari struk.\n\n"

                "Pastikan nominal pembayaran "
                "terlihat jelas pada foto."

            )

            return

        # ======================================
        # PENDING RECEIPT
        # ======================================

        context.user_data[
            "pending_receipt"
        ] = {

            "user_id": user_id,

            "merchant": merchant,

            "date": expense_date,

            "amount": total,

            "category": category,

            "items": items,

            "image_path": file_path,

            "raw_text": result[
                "raw_text"
            ],

        }

        # ======================================
        # DATE TEXT
        # ======================================

        if expense_date:

            date_text = (
                expense_date.strftime(
                    "%d-%m-%Y"
                )
            )

        else:

            date_text = (
                "Tidak terdeteksi"
            )

        # ======================================
        # ITEM TEXT
        # ======================================

        if items:

            item_text = (
                "\n🧾 *Item:*\n"
            )

            for item in items:

                item_text += (
                    f"• {item['name']}"
                )

                if item[
                    "quantity"
                ] > 1:

                    item_text += (
                        f" x{item['quantity']}"
                    )

                item_text += (
                    " — "
                    f"{format_rupiah(item['amount'])}\n"
                )

        else:

            item_text = (
                "\n🧾 *Item:* "
                "Tidak terdeteksi\n"
            )

        # ======================================
        # CONFIRMATION
        # ======================================

        message = (

            "🧾 *Struk berhasil dibaca!*\n\n"

            f"🏪 *Toko:* {merchant}\n"

            f"📅 *Tanggal:* {date_text}\n"

            f"💰 *Total:* "
            f"{format_rupiah(total)}\n"

            f"🏷️ *Kategori:* {category}\n"

            f"{item_text}\n"

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

        await processing_message.edit_text(

            message,

            reply_markup=reply_markup,

            parse_mode="Markdown",

        )

    except Exception as error:

        print(
            "\nReceipt OCR error:"
        )

        print(
            repr(error)
        )

        await processing_message.edit_text(

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

    pending = (
        context.user_data.get(
            "pending_receipt"
        )
    )

    # ==========================================
    # BATAL
    # ==========================================

    if query.data == "receipt_cancel":

        image_path = None

        if pending:

            image_path = (
                pending.get(
                    "image_path"
                )
            )

        context.user_data.pop(
            "pending_receipt",
            None,
        )

        if image_path:

            if os.path.exists(
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
            # EXPENSE
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

                expense_date=pending[
                    "date"
                ],

            )

            db.add(
                expense
            )

            # ==================================
            # ITEMS
            # ==================================

            for item_data in pending[
                "items"
            ]:

                item = ExpenseItem(

                    expense=expense,

                    name=item_data[
                        "name"
                    ],

                    quantity=item_data[
                        "quantity"
                    ],

                    amount=item_data[
                        "amount"
                    ],

                )

                db.add(
                    item
                )

            # ==================================
            # COMMIT
            # ==================================

            db.commit()

            db.refresh(
                expense
            )

            # ==================================
            # HAPUS FOTO
            # ==================================

            image_path = (
                pending.get(
                    "image_path"
                )
            )

            if image_path:

                if os.path.exists(
                    image_path
                ):

                    try:

                        os.remove(
                            image_path
                        )

                    except OSError:

                        pass

            # ==================================
            # JUMLAH ITEM
            # ==================================

            item_count = len(
                pending["items"]
            )

            # ==================================
            # RESPONSE
            # ==================================

            await query.edit_message_text(

                "✅ *Struk berhasil disimpan!*\n\n"

                f"🏪 *Toko:* "
                f"{expense.description}\n"

                f"💰 *Total:* "
                f"{format_rupiah(expense.amount)}\n"

                f"🏷️ *Kategori:* "
                f"{expense.category}\n"

                f"🧾 *Item:* "
                f"{item_count}\n\n"

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
                "\nReceipt save error:"
            )

            print(
                repr(error)
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