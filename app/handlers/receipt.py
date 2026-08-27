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

from app.handlers.budget import (
    send_budget_warning,
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

    if amount is None:
        amount = 0

    return f"Rp{int(amount):,}".replace(
        ",",
        ".",
    )


# ============================================================
# NORMALIZE AMOUNT
# ============================================================

def normalize_amount(
    value: str,
):

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

    if "." in value:

        parts = value.split(".")

        if all(
            len(part) == 3
            for part in parts[1:]
        ):

            value = "".join(parts)

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

    image = Image.open(
        image_path
    )

    image = ImageOps.grayscale(
        image
    )

    width, height = image.size

    image = image.resize(
        (
            width * 2,
            height * 2,
        )
    )

    enhancer = ImageEnhance.Contrast(
        image
    )

    image = enhancer.enhance(
        2.0
    )

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

    amounts = []

    patterns = [

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

    for pattern in patterns:

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

        return max(amounts)

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

        return max(amounts)

    return None


# ============================================================
# VALIDATE MERCHANT
# ============================================================

def is_valid_merchant(
    value: str,
) -> bool:

    if not value:

        return False

    value = value.strip()

    if len(value) < 3:

        return False

    if not re.search(
        r"[A-Za-z]",
        value,
    ):

        return False

    if re.fullmatch(
        r"[\d\s.,:/\-]+",
        value,
    ):

        return False

    if re.fullmatch(
        r"(rp|idr)?\s*[\d.,]+",
        value,
        re.IGNORECASE,
    ):

        return False

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

    # --------------------------------------------------------
    # Berdasarkan label
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # 25/07/2026
    # 25-07-2026
    # 25.07.2026
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # 25 Jul 2026
    # 25 July 2026
    # --------------------------------------------------------

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

        amount = normalize_amount(
            match.group(2)
        )

        if not name:

            continue

        if amount is None:

            continue

        if amount <= 0:

            continue

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
# SHOW RECEIPT CONFIRMATION
# ============================================================

async def show_receipt_confirmation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    pending = context.user_data.get(
        "pending_receipt"
    )

    if not pending:

        return

    merchant = pending.get(
        "merchant",
        "Tidak diketahui",
    )

    expense_date = pending.get(
        "date"
    )

    amount = pending.get(
        "amount",
        0,
    )

    category = pending.get(
        "category",
        "Lainnya",
    )

    items = pending.get(
        "items",
        [],
    )

    # ========================================================
    # DATE
    # ========================================================

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

    # ========================================================
    # ITEMS
    # ========================================================

    if items:

        item_text = (
            "\n🧾 *Item:*\n"
        )

        for item in items:

            item_text += (
                f"• {item['name']}"
            )

            if item["quantity"] > 1:

                item_text += (
                    f" x{item['quantity']}"
                )

            item_text += (

                " — "

                f"{format_rupiah(item['amount'])}"

                "\n"

            )

    else:

        item_text = (
            "\n🧾 *Item:* "
            "Tidak terdeteksi\n"
        )

    # ========================================================
    # MESSAGE
    # ========================================================

    message = (

        "🧾 *Data Struk*\n\n"

        f"🏪 *Toko:* {merchant}\n"

        f"📅 *Tanggal:* {date_text}\n"

        f"💰 *Total:* "
        f"{format_rupiah(amount)}\n"

        f"🏷️ *Kategori:* {category}\n"

        f"{item_text}\n"

        "Apakah data ini sudah benar?"

    )

    keyboard = [

        [

            InlineKeyboardButton(

                "✏️ Edit",

                callback_data=(
                    "receipt_edit_menu"
                ),

            ),

            InlineKeyboardButton(

                "✅ Simpan",

                callback_data=(
                    "receipt_save"
                ),

            ),

        ],

        [

            InlineKeyboardButton(

                "❌ Batal",

                callback_data=(
                    "receipt_cancel"
                ),

            ),

        ],

    ]

    markup = InlineKeyboardMarkup(
        keyboard
    )

    if update.callback_query:

        await update.callback_query.edit_message_text(

            message,

            reply_markup=markup,

            parse_mode="Markdown",

        )

    elif update.message:

        await update.message.reply_text(

            message,

            reply_markup=markup,

            parse_mode="Markdown",

        )


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

    photo = (
        update.message.photo[-1]
    )

    telegram_file = (
        await context.bot.get_file(
            photo.file_id
        )
    )

    file_path = (
        f"temp_receipt_{user_id}.jpg"
    )

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

        # ====================================================
        # DEBUG OCR
        # ====================================================

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
            f"Merchant : "
            f"{result['merchant']}"
        )

        print(
            f"Date     : "
            f"{result['date']}"
        )

        print(
            f"Total    : "
            f"{result['total']}"
        )

        print(
            f"Category : "
            f"{result['category']}"
        )

        print(
            f"Items    : "
            f"{result['items']}"
        )

        print(
            "================================\n"
        )

        # ====================================================
        # TOTAL TIDAK DITEMUKAN
        # ====================================================

        if result["total"] is None:

            await processing_message.edit_text(

                "❌ Saya belum bisa menemukan "
                "total pembayaran dari struk.\n\n"

                "Pastikan nominal pembayaran "
                "terlihat jelas pada foto."

            )

            return

        # ====================================================
        # SAVE PENDING RECEIPT
        # ====================================================

        context.user_data[
            "pending_receipt"
        ] = {

            "user_id": user_id,

            "merchant": result[
                "merchant"
            ],

            "date": result[
                "date"
            ],

            "amount": result[
                "total"
            ],

            "category": result[
                "category"
            ],

            "items": result[
                "items"
            ],

            "image_path": file_path,

            "raw_text": result[
                "raw_text"
            ],

        }

        await processing_message.delete()

        await show_receipt_confirmation(
            update,
            context,
        )

    except Exception as error:

        print(
            "Receipt OCR error:"
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

    pending = context.user_data.get(
        "pending_receipt"
    )

    # ========================================================
    # CANCEL
    # ========================================================

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

    # ========================================================
    # SAVE
    # ========================================================

    if query.data == "receipt_save":

        if not pending:

            await query.edit_message_text(

                "❌ Data struk "
                "sudah tidak tersedia."

            )

            return

        db = SessionLocal()

        try:

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

            # =================================================
            # SAVE ITEMS
            # =================================================

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

            # =================================================
            # COMMIT
            # =================================================

            db.commit()

            db.refresh(
                expense
            )

            # =================================================
            # DELETE TEMP IMAGE
            # =================================================

            image_path = pending.get(
                "image_path"
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

            # =================================================
            # SUCCESS MESSAGE
            # =================================================

            item_count = len(
                pending["items"]
            )

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

            # =================================================
            # BUDGET WARNING
            # =================================================

            await send_budget_warning(
                update
            )

            # =================================================
            # CLEAR PENDING
            # =================================================

            context.user_data.pop(
                "pending_receipt",
                None,
            )

        except Exception as error:

            print(
                "Receipt save error:"
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
# EDIT RECEIPT MENU
# ============================================================

async def receipt_edit_menu(
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

    if not pending:

        await query.edit_message_text(

            "❌ Data struk "
            "sudah tidak tersedia."

        )

        return

    keyboard = [

        [

            InlineKeyboardButton(

                "🏪 Toko",

                callback_data=(
                    "receipt_edit_merchant"
                ),

            ),

            InlineKeyboardButton(

                "📅 Tanggal",

                callback_data=(
                    "receipt_edit_date"
                ),

            ),

        ],

        [

            InlineKeyboardButton(

                "💰 Nominal",

                callback_data=(
                    "receipt_edit_amount"
                ),

            ),

            InlineKeyboardButton(

                "🏷️ Kategori",

                callback_data=(
                    "receipt_edit_category"
                ),

            ),

        ],

        [

            InlineKeyboardButton(

                "↩️ Kembali",

                callback_data=(
                    "receipt_edit_back"
                ),

            ),

        ],

    ]

    await query.edit_message_text(

        "✏️ *Apa yang ingin diubah?*",

        reply_markup=(
            InlineKeyboardMarkup(
                keyboard
            )
        ),

        parse_mode="Markdown",

    )


# ============================================================
# EDIT FIELD
# ============================================================

async def receipt_edit_field(
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

    if not pending:

        await query.edit_message_text(

            "❌ Data struk "
            "sudah tidak tersedia."

        )

        return

    field = query.data.replace(
        "receipt_edit_",
        "",
    )

    context.user_data[
        "editing_receipt_field"
    ] = field

    field_names = {

        "merchant": "🏪 Toko",

        "date": "📅 Tanggal",

        "amount": "💰 Nominal",

        "category": "🏷️ Kategori",

    }

    current_value = pending.get(
        field
    )

    if field == "date":

        if current_value:

            current_value = (
                current_value.strftime(
                    "%d-%m-%Y"
                )
            )

        else:

            current_value = (
                "Tidak terdeteksi"
            )

    elif field == "amount":

        current_value = format_rupiah(
            current_value
        )

    await query.edit_message_text(

        f"✏️ *Edit "
        f"{field_names.get(field, field)}*\n\n"

        f"Nilai sekarang: "
        f"`{current_value}`\n\n"

        "Kirim nilai baru melalui chat.",

        parse_mode="Markdown",

    )


# ============================================================
# HANDLE EDIT TEXT
# ============================================================

async def receipt_edit_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:

        return

    field = context.user_data.get(
        "editing_receipt_field"
    )

    if not field:

        return

    pending = context.user_data.get(
        "pending_receipt"
    )

    if not pending:

        context.user_data.pop(
            "editing_receipt_field",
            None,
        )

        return

    value = update.message.text.strip()

    # ========================================================
    # MERCHANT
    # ========================================================

    if field == "merchant":

        if len(value) < 2:

            await update.message.reply_text(

                "❌ Nama toko terlalu pendek."

            )

            return

        pending[
            "merchant"
        ] = value

    # ========================================================
    # DATE
    # ========================================================

    elif field == "date":

        parsed_date = None

        formats = [

            "%d-%m-%Y",

            "%d/%m/%Y",

            "%d.%m.%Y",

        ]

        for fmt in formats:

            try:

                parsed_date = (
                    datetime.strptime(
                        value,
                        fmt,
                    ).date()
                )

                break

            except ValueError:

                continue

        if not parsed_date:

            await update.message.reply_text(

                "❌ Format tanggal salah.\n\n"

                "Gunakan:\n"
                "`25-07-2026`",

                parse_mode="Markdown",

            )

            return

        pending[
            "date"
        ] = parsed_date

    # ========================================================
    # AMOUNT
    # ========================================================

    elif field == "amount":

        amount = normalize_amount(
            value
        )

        if not amount or amount <= 0:

            await update.message.reply_text(

                "❌ Nominal tidak valid.\n\n"

                "Contoh:\n"
                "`25000`\n"
                "`25.000`",

                parse_mode="Markdown",

            )

            return

        pending[
            "amount"
        ] = amount

    # ========================================================
    # CATEGORY
    # ========================================================

    elif field == "category":

        categories = [

            "Makanan",

            "Transportasi",

            "Belanja",

            "Kesehatan",

            "Hiburan",

            "Lainnya",

        ]

        matched_category = None

        for category in categories:

            if (
                value.lower()
                == category.lower()
            ):

                matched_category = (
                    category
                )

                break

        if not matched_category:

            await update.message.reply_text(

                "❌ Kategori tidak valid.\n\n"

                "Pilih salah satu:\n"

                "• Makanan\n"
                "• Transportasi\n"
                "• Belanja\n"
                "• Kesehatan\n"
                "• Hiburan\n"
                "• Lainnya"

            )

            return

        pending[
            "category"
        ] = matched_category

    # ========================================================
    # CLEAR EDIT STATE
    # ========================================================

    context.user_data.pop(
        "editing_receipt_field",
        None,
    )

    # ========================================================
    # SHOW UPDATED DATA
    # ========================================================

    await show_receipt_confirmation(
        update,
        context,
    )


# ============================================================
# EDIT BACK
# ============================================================

async def receipt_edit_back(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:

        return

    await query.answer()

    await show_receipt_confirmation(
        update,
        context,
    )


# ============================================================
# CALLBACK HANDLERS
# ============================================================

receipt_callback_handler = (
    CallbackQueryHandler(

        receipt_callback,

        pattern=(
            r"^receipt_(save|cancel)$"
        ),

    )
)


receipt_edit_callback_handler = (
    CallbackQueryHandler(

        receipt_edit_menu,

        pattern=(
            r"^receipt_edit_menu$"
        ),

    )
)


receipt_edit_field_callback_handler = (
    CallbackQueryHandler(

        receipt_edit_field,

        pattern=(
            r"^receipt_edit_"
            r"(merchant|date|amount|category)$"
        ),

    )
)


receipt_edit_back_callback_handler = (
    CallbackQueryHandler(

        receipt_edit_back,

        pattern=(
            r"^receipt_edit_back$"
        ),

    )
)