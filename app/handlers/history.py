from sqlalchemy import select

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
# CONSTANT
# ============================================================

PER_PAGE = 5


# ============================================================
# FORMAT RUPIAH
# ============================================================

def format_rupiah(amount: int) -> str:
    return f"Rp{amount:,}".replace(",", ".")


# ============================================================
# CATEGORY ICON
# ============================================================

def category_icon(category: str) -> str:

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
# GET EXPENSES
# ============================================================

def get_expenses(
    user_id: int,
    page: int,
):

    offset = page * PER_PAGE

    db = SessionLocal()

    try:

        statement = (
            select(Expense)
            .where(
                Expense.user_id == user_id
            )
            .order_by(
                Expense.expense_date.desc(),
                Expense.created_at.desc(),
            )
            .offset(offset)
            .limit(PER_PAGE + 1)
        )

        expenses = db.scalars(
            statement
        ).all()

        has_next = (
            len(expenses)
            > PER_PAGE
        )

        return (
            expenses[:PER_PAGE],
            has_next,
        )

    finally:

        db.close()


# ============================================================
# BUILD HISTORY MESSAGE
# ============================================================

def build_history_message(
    expenses,
    page: int,
) -> str:

    message = (
        "📋 *Riwayat Pengeluaran*\n\n"
    )

    start_number = (
        page * PER_PAGE
    ) + 1

    for index, expense in enumerate(
        expenses,
        start=start_number,
    ):

        if expense.expense_date:

            date_text = (
                expense.expense_date.strftime(
                    "%d-%m-%Y"
                )
            )

        else:

            date_text = "--"

        icon = category_icon(
            expense.category
        )

        description = (
            expense.description
            or "Transaksi"
        )

        message += (

            f"*{index}. "
            f"{icon} {description}*\n"

            f"   📅 {date_text}\n"

            f"   💰 "
            f"{format_rupiah(expense.amount)}\n"

            f"   🏷️ {expense.category}\n\n"

        )

    message += (
        f"📄 Halaman {page + 1}"
    )

    return message


# ============================================================
# BUILD HISTORY KEYBOARD
# ============================================================

def build_history_keyboard(
    expenses,
    page: int,
    has_next: bool,
):

    keyboard = []

    # --------------------------------------------------------
    # DETAIL BUTTON
    # --------------------------------------------------------

    for expense in expenses:

        description = (
            expense.description
            or "Transaksi"
        )

        if len(description) > 20:

            description = (
                description[:20]
                + "..."
            )

        keyboard.append(

            [

                InlineKeyboardButton(

                    f"🔎 {description}",

                    callback_data=(
                        f"expense_detail_"
                        f"{expense.id}_"
                        f"{page}"
                    ),

                ),

            ]

        )

    # --------------------------------------------------------
    # PAGINATION
    # --------------------------------------------------------

    navigation = []

    if page > 0:

        navigation.append(

            InlineKeyboardButton(

                "⬅️ Sebelumnya",

                callback_data=(
                    f"history_page_"
                    f"{page - 1}"
                ),

            )

        )

    if has_next:

        navigation.append(

            InlineKeyboardButton(

                "➡️ Berikutnya",

                callback_data=(
                    f"history_page_"
                    f"{page + 1}"
                ),

            )

        )

    if navigation:

        keyboard.append(
            navigation
        )

    return InlineKeyboardMarkup(
        keyboard
    )


# ============================================================
# SHOW HISTORY
# ============================================================

async def show_history(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    page: int = 0,
):

    if not update.effective_user:

        return

    user_id = (
        update.effective_user.id
    )

    if page < 0:

        page = 0

    expenses, has_next = (
        get_expenses(
            user_id,
            page,
        )
    )

    # ========================================================
    # EMPTY
    # ========================================================

    if not expenses:

        if page > 0:

            await show_history(
                update,
                context,
                page=page - 1,
            )

            return

        message = (

            "📋 *Riwayat Pengeluaran*\n\n"

            "Belum ada transaksi."

        )

        if update.callback_query:

            await update.callback_query.edit_message_text(

                message,

                parse_mode="Markdown",

            )

        elif update.message:

            await update.message.reply_text(

                message,

                parse_mode="Markdown",

            )

        return

    # ========================================================
    # MESSAGE
    # ========================================================

    message = build_history_message(
        expenses,
        page,
    )

    markup = build_history_keyboard(
        expenses,
        page,
        has_next,
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
# /RIWAYAT
# ============================================================

async def history_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await show_history(
        update,
        context,
        page=0,
    )


# ============================================================
# PAGINATION
# ============================================================

async def history_page(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:

        return

    await query.answer()

    try:

        page = int(
            query.data.replace(
                "history_page_",
                "",
            )
        )

    except (
        ValueError,
        AttributeError,
    ):

        return

    if page < 0:

        page = 0

    await show_history(
        update,
        context,
        page=page,
    )


# ============================================================
# EXPENSE DETAIL
# ============================================================

async def expense_detail(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:

        return

    await query.answer()

    try:

        parts = query.data.split(
            "_"
        )

        # expense_detail_ID_PAGE
        expense_id = int(
            parts[2]
        )

        page = int(
            parts[3]
        )

    except (
        ValueError,
        IndexError,
    ):

        await query.edit_message_text(
            "❌ Data transaksi tidak valid."
        )

        return

    if not update.effective_user:

        return

    user_id = (
        update.effective_user.id
    )

    db = SessionLocal()

    try:

        statement = (
            select(Expense)
            .where(
                Expense.id == expense_id,
                Expense.user_id == user_id,
            )
        )

        expense = db.scalar(
            statement
        )

        if not expense:

            await query.edit_message_text(
                "❌ Transaksi tidak ditemukan."
            )

            return

        if expense.expense_date:

            date_text = (
                expense.expense_date.strftime(
                    "%d-%m-%Y"
                )
            )

        else:

            date_text = "--"

        # ====================================================
        # ITEMS
        # ====================================================

        item_statement = (
            select(ExpenseItem)
            .where(
                ExpenseItem.expense_id
                == expense.id
            )
            .order_by(
                ExpenseItem.id.asc()
            )
        )

        items = db.scalars(
            item_statement
        ).all()

        # ====================================================
        # MESSAGE
        # ====================================================

        message = (

            "🧾 *Detail Transaksi*\n\n"

            f"🏪 *Toko:* "
            f"{expense.description}\n"

            f"📅 *Tanggal:* "
            f"{date_text}\n"

            f"💰 *Total:* "
            f"{format_rupiah(expense.amount)}\n"

            f"🏷️ *Kategori:* "
            f"{expense.category}\n\n"

        )

        if items:

            message += (
                "🛍️ *Item:*\n"
            )

            for item in items:

                item_name = (
                    item.name
                    or "Item"
                )

                quantity = (
                    item.quantity
                    or 1
                )

                item_amount = (
                    item.amount
                    or 0
                )

                if quantity > 1:

                    message += (

                        f"• {item_name} "
                        f"x{quantity} — "
                        f"{format_rupiah(item_amount)}\n"

                    )

                else:

                    message += (

                        f"• {item_name} — "
                        f"{format_rupiah(item_amount)}\n"

                    )

        else:

            message += (

                "🛍️ *Item:*\n"

                "Tidak ada detail item."

            )

        # ====================================================
        # KEYBOARD
        # ====================================================

        keyboard = [

            [

                InlineKeyboardButton(

                    "✏️ Edit",

                    callback_data=(
                        f"expense_edit_"
                        f"{expense.id}_"
                        f"{page}"
                    ),

                ),

            ],

            [

                InlineKeyboardButton(

                    "🗑️ Hapus",

                    callback_data=(
                        f"expense_delete_"
                        f"{expense.id}_"
                        f"{page}"
                    ),

                ),

            ],

            [

                InlineKeyboardButton(

                    "⬅️ Kembali",

                    callback_data=(
                        f"history_back_"
                        f"{page}"
                    ),

                ),

            ],

        ]

        await query.edit_message_text(

            message,

            reply_markup=(
                InlineKeyboardMarkup(
                    keyboard
                )
            ),

            parse_mode="Markdown",

        )

    finally:

        db.close()


# ============================================================
# BACK TO HISTORY
# ============================================================

async def history_back(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:

        return

    await query.answer()

    try:

        page = int(
            query.data.replace(
                "history_back_",
                "",
            )
        )

    except ValueError:

        page = 0

    await show_history(
        update,
        context,
        page=page,
    )


# ============================================================
# EDIT MENU
# ============================================================

async def edit_expense_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:

        return

    await query.answer()

    try:

        parts = query.data.split(
            "_"
        )

        # expense_edit_ID_PAGE
        expense_id = int(
            parts[2]
        )

        page = int(
            parts[3]
        )

    except (
        ValueError,
        IndexError,
    ):

        await query.edit_message_text(
            "❌ Data transaksi tidak valid."
        )

        return

    if not update.effective_user:

        return

    user_id = (
        update.effective_user.id
    )

    db = SessionLocal()

    try:

        statement = (
            select(Expense)
            .where(
                Expense.id == expense_id,
                Expense.user_id == user_id,
            )
        )

        expense = db.scalar(
            statement
        )

        if not expense:

            await query.edit_message_text(
                "❌ Transaksi tidak ditemukan."
            )

            return

        context.user_data[
            "editing_expense_id"
        ] = expense_id

        context.user_data[
            "editing_expense_page"
        ] = page

        message = (

            "✏️ *Edit Transaksi*\n\n"

            f"🏪 {expense.description}\n"

            f"💰 "
            f"{format_rupiah(expense.amount)}\n"

            f"🏷️ {expense.category}\n\n"

            "Pilih data yang ingin diubah:"

        )

        keyboard = [

            [

                InlineKeyboardButton(
                    "🏪 Toko",
                    callback_data=(
                        f"edit_field_"
                        f"merchant"
                    ),
                ),

                InlineKeyboardButton(
                    "📅 Tanggal",
                    callback_data=(
                        f"edit_field_"
                        f"date"
                    ),
                ),

            ],

            [

                InlineKeyboardButton(
                    "💰 Nominal",
                    callback_data=(
                        f"edit_field_"
                        f"amount"
                    ),
                ),

                InlineKeyboardButton(
                    "🏷️ Kategori",
                    callback_data=(
                        f"edit_field_"
                        f"category"
                    ),
                ),

            ],

            [

                InlineKeyboardButton(
                    "⬅️ Kembali",
                    callback_data=(
                        f"history_back_"
                        f"{page}"
                    ),
                ),

            ],

        ]

        await query.edit_message_text(

            message,

            reply_markup=(
                InlineKeyboardMarkup(
                    keyboard
                )
            ),

            parse_mode="Markdown",

        )

    finally:

        db.close()


# ============================================================
# SELECT EDIT FIELD
# ============================================================

async def select_edit_field(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:

        return

    await query.answer()

    expense_id = context.user_data.get(
        "editing_expense_id"
    )

    page = context.user_data.get(
        "editing_expense_page",
        0,
    )

    if not expense_id:

        await query.edit_message_text(

            "❌ Sesi edit sudah tidak tersedia."

        )

        return

    field = query.data.replace(
        "edit_field_",
        "",
    )

    valid_fields = [
        "merchant",
        "date",
        "amount",
        "category",
    ]

    if field not in valid_fields:

        await query.edit_message_text(
            "❌ Field tidak valid."
        )

        return

    context.user_data[
        "editing_expense_field"
    ] = field

    field_names = {

        "merchant": "🏪 Toko",

        "date": "📅 Tanggal",

        "amount": "💰 Nominal",

        "category": "🏷️ Kategori",

    }

    instruction = {

        "merchant": (
            "Kirim nama toko baru."
        ),

        "date": (
            "Kirim tanggal baru.\n\n"
            "Format: `25-07-2026`"
        ),

        "amount": (
            "Kirim nominal baru.\n\n"
            "Contoh: `25000`"
        ),

        "category": (

            "Kirim kategori baru.\n\n"

            "Pilihan:\n"
            "• Makanan\n"
            "• Transportasi\n"
            "• Belanja\n"
            "• Kesehatan\n"
            "• Hiburan\n"
            "• Lainnya"

        ),

    }

    message = (

        f"✏️ *Edit "
        f"{field_names[field]}*\n\n"

        f"{instruction[field]}"

    )

    keyboard = [

        [

            InlineKeyboardButton(

                "❌ Batal",

                callback_data=(
                    f"edit_cancel_"
                    f"{page}"
                ),

            ),

        ]

    ]

    await query.edit_message_text(

        message,

        reply_markup=(
            InlineKeyboardMarkup(
                keyboard
            )
        ),

        parse_mode="Markdown",

    )


# ============================================================
# HANDLE EDIT TEXT
# ============================================================

async def edit_expense_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:

        return False

    field = context.user_data.get(
        "editing_expense_field"
    )

    expense_id = context.user_data.get(
        "editing_expense_id"
    )

    page = context.user_data.get(
        "editing_expense_page",
        0,
    )

    if not field or not expense_id:

        return False

    value = update.message.text.strip()

    if not value:

        await update.message.reply_text(
            "❌ Nilai tidak boleh kosong."
        )

        return True

    # ========================================================
    # MERCHANT
    # ========================================================

    if field == "merchant":

        if len(value) < 2:

            await update.message.reply_text(
                "❌ Nama toko terlalu pendek."
            )

            return True

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

        for date_format in formats:

            try:

                parsed_date = (
                    __import__(
                        "datetime"
                    )
                    .datetime
                    .strptime(
                        value,
                        date_format,
                    )
                    .date()
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

            return True

        value = parsed_date

    # ========================================================
    # AMOUNT
    # ========================================================

    elif field == "amount":

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
                "`25000`\n"
                "`25.000`",

                parse_mode="Markdown",

            )

            return True

        value = int(
            clean_value
        )

        if value <= 0:

            await update.message.reply_text(
                "❌ Nominal harus lebih dari 0."
            )

            return True

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

                "Pilih:\n"

                "• Makanan\n"
                "• Transportasi\n"
                "• Belanja\n"
                "• Kesehatan\n"
                "• Hiburan\n"
                "• Lainnya"

            )

            return True

        value = matched_category

    # ========================================================
    # UPDATE DATABASE
    # ========================================================

    if not update.effective_user:

        return True

    user_id = (
        update.effective_user.id
    )

    db = SessionLocal()

    try:

        statement = (
            select(Expense)
            .where(
                Expense.id == expense_id,
                Expense.user_id == user_id,
            )
        )

        expense = db.scalar(
            statement
        )

        if not expense:

            await update.message.reply_text(

                "❌ Transaksi tidak ditemukan."

            )

            return True

        if field == "merchant":

            expense.description = value

        elif field == "date":

            expense.expense_date = value

        elif field == "amount":

            expense.amount = value

        elif field == "category":

            expense.category = value

        db.commit()

        # ====================================================
        # CLEAR EDIT STATE
        # ====================================================

        context.user_data.pop(
            "editing_expense_field",
            None,
        )

        context.user_data.pop(
            "editing_expense_id",
            None,
        )

        context.user_data.pop(
            "editing_expense_page",
            None,
        )

        await update.message.reply_text(

            "✅ *Transaksi berhasil diperbarui!*",

            parse_mode="Markdown",

        )

        # ====================================================
        # SHOW UPDATED DETAIL
        # ====================================================

        await send_expense_detail(

            update,

            expense_id,

        )

    except Exception as error:

        print(
            "Edit expense error:"
        )

        print(
            repr(error)
        )

        db.rollback()

        await update.message.reply_text(

            "❌ Terjadi kesalahan "
            "saat memperbarui transaksi."

        )

    finally:

        db.close()

    return True


# ============================================================
# SEND EXPENSE DETAIL
# ============================================================

async def send_expense_detail(
    update: Update,
    expense_id: int,
):

    if not update.effective_user:

        return

    user_id = (
        update.effective_user.id
    )

    db = SessionLocal()

    try:

        statement = (
            select(Expense)
            .where(
                Expense.id == expense_id,
                Expense.user_id == user_id,
            )
        )

        expense = db.scalar(
            statement
        )

        if not expense:

            return

        if expense.expense_date:

            date_text = (
                expense.expense_date.strftime(
                    "%d-%m-%Y"
                )
            )

        else:

            date_text = "--"

        item_statement = (
            select(ExpenseItem)
            .where(
                ExpenseItem.expense_id
                == expense.id
            )
            .order_by(
                ExpenseItem.id.asc()
            )
        )

        items = db.scalars(
            item_statement
        ).all()

        message = (

            "🧾 *Detail Transaksi*\n\n"

            f"🏪 *Toko:* "
            f"{expense.description}\n"

            f"📅 *Tanggal:* "
            f"{date_text}\n"

            f"💰 *Total:* "
            f"{format_rupiah(expense.amount)}\n"

            f"🏷️ *Kategori:* "
            f"{expense.category}\n\n"

        )

        if items:

            message += (
                "🛍️ *Item:*\n"
            )

            for item in items:

                item_name = (
                    item.name
                    or "Item"
                )

                quantity = (
                    item.quantity
                    or 1
                )

                item_amount = (
                    item.amount
                    or 0
                )

                message += (

                    f"• {item_name}"

                )

                if quantity > 1:

                    message += (
                        f" x{quantity}"
                    )

                message += (

                    " — "
                    f"{format_rupiah(item_amount)}\n"

                )

        else:

            message += (

                "🛍️ *Item:*\n"

                "Tidak ada detail item."

            )

        keyboard = [

            [

                InlineKeyboardButton(

                    "✏️ Edit",

                    callback_data=(
                        f"expense_edit_"
                        f"{expense.id}_0"
                    ),

                ),

                InlineKeyboardButton(

                    "🗑️ Hapus",

                    callback_data=(
                        f"expense_delete_"
                        f"{expense.id}_0"
                    ),

                ),

            ],

            [

                InlineKeyboardButton(

                    "📋 Riwayat",

                    callback_data=(
                        "history_page_0"
                    ),

                ),

            ],

        ]

        await update.message.reply_text(

            message,

            reply_markup=(
                InlineKeyboardMarkup(
                    keyboard
                )
            ),

            parse_mode="Markdown",

        )

    finally:

        db.close()


# ============================================================
# CANCEL EDIT
# ============================================================

async def cancel_edit_expense(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:

        return

    await query.answer(
        "Edit dibatalkan."
    )

    try:

        page = int(
            query.data.replace(
                "edit_cancel_",
                "",
            )
        )

    except ValueError:

        page = 0

    context.user_data.pop(
        "editing_expense_field",
        None,
    )

    context.user_data.pop(
        "editing_expense_id",
        None,
    )

    context.user_data.pop(
        "editing_expense_page",
        None,
    )

    await show_history(
        update,
        context,
        page=page,
    )


# ============================================================
# DELETE CONFIRMATION
# ============================================================

async def delete_expense_confirmation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:

        return

    await query.answer()

    try:

        parts = query.data.split(
            "_"
        )

        expense_id = int(
            parts[2]
        )

        page = int(
            parts[3]
        )

    except (
        ValueError,
        IndexError,
    ):

        await query.edit_message_text(

            "❌ Data transaksi tidak valid."

        )

        return

    if not update.effective_user:

        return

    user_id = (
        update.effective_user.id
    )

    db = SessionLocal()

    try:

        statement = (
            select(Expense)
            .where(
                Expense.id == expense_id,
                Expense.user_id == user_id,
            )
        )

        expense = db.scalar(
            statement
        )

        if not expense:

            await query.edit_message_text(

                "❌ Transaksi tidak ditemukan."

            )

            return

        if expense.expense_date:

            date_text = (
                expense.expense_date.strftime(
                    "%d-%m-%Y"
                )
            )

        else:

            date_text = "--"

        message = (

            "⚠️ *Konfirmasi Penghapusan*\n\n"

            f"🏪 *{expense.description}*\n"

            f"📅 {date_text}\n"

            f"💰 "
            f"{format_rupiah(expense.amount)}\n"

            f"🏷️ {expense.category}\n\n"

            "Yakin ingin menghapus "
            "transaksi ini?"

        )

        keyboard = [

            [

                InlineKeyboardButton(

                    "✅ Ya, Hapus",

                    callback_data=(
                        f"expense_confirm_delete_"
                        f"{expense.id}_"
                        f"{page}"
                    ),

                ),

                InlineKeyboardButton(

                    "❌ Batal",

                    callback_data=(
                        f"expense_delete_cancel_"
                        f"{page}"
                    ),

                ),

            ]

        ]

        await query.edit_message_text(

            message,

            reply_markup=(
                InlineKeyboardMarkup(
                    keyboard
                )
            ),

            parse_mode="Markdown",

        )

    finally:

        db.close()


# ============================================================
# DELETE EXPENSE
# ============================================================

async def delete_expense(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:

        return

    await query.answer()

    try:

        parts = query.data.split(
            "_"
        )

        expense_id = int(
            parts[3]
        )

        page = int(
            parts[4]
        )

    except (
        ValueError,
        IndexError,
    ):

        await query.edit_message_text(

            "❌ Data transaksi tidak valid."

        )

        return

    if not update.effective_user:

        return

    user_id = (
        update.effective_user.id
    )

    db = SessionLocal()

    try:

        statement = (
            select(Expense)
            .where(
                Expense.id == expense_id,
                Expense.user_id == user_id,
            )
        )

        expense = db.scalar(
            statement
        )

        if not expense:

            await query.edit_message_text(

                "❌ Transaksi tidak ditemukan."

            )

            return

        description = (
            expense.description
        )

        amount = (
            expense.amount
        )

        db.delete(
            expense
        )

        db.commit()

        await query.edit_message_text(

            "✅ *Transaksi berhasil dihapus!*\n\n"

            f"🏪 {description}\n"

            f"💰 "
            f"{format_rupiah(amount)}",

            parse_mode="Markdown",

        )

        expenses, has_next = (
            get_expenses(
                user_id,
                page,
            )
        )

        if expenses:

            message = (
                build_history_message(
                    expenses,
                    page,
                )
            )

            markup = (
                build_history_keyboard(
                    expenses,
                    page,
                    has_next,
                )
            )

            await query.message.reply_text(

                message,

                reply_markup=markup,

                parse_mode="Markdown",

            )

        elif page > 0:

            await show_history(

                update,

                context,

                page=page - 1,

            )

        else:

            await query.message.reply_text(

                "📋 *Riwayat Pengeluaran*\n\n"
                "Belum ada transaksi.",

                parse_mode="Markdown",

            )

    except Exception as error:

        print(
            "Delete expense error:"
        )

        print(
            repr(error)
        )

        db.rollback()

        await query.edit_message_text(

            "❌ Terjadi kesalahan "
            "saat menghapus transaksi."

        )

    finally:

        db.close()


# ============================================================
# CANCEL DELETE
# ============================================================

async def cancel_delete_expense(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:

        return

    await query.answer(
        "Penghapusan dibatalkan."
    )

    try:

        page = int(
            query.data.replace(
                "expense_delete_cancel_",
                "",
            )
        )

    except ValueError:

        page = 0

    await show_history(
        update,
        context,
        page=page,
    )


# ============================================================
# CALLBACK HANDLERS
# ============================================================

history_callback_handler = (
    CallbackQueryHandler(

        history_page,

        pattern=(
            r"^history_page_\d+$"
        ),

    )
)


history_detail_handler = (
    CallbackQueryHandler(

        expense_detail,

        pattern=(
            r"^expense_detail_\d+_\d+$"
        ),

    )
)


history_back_handler = (
    CallbackQueryHandler(

        history_back,

        pattern=(
            r"^history_back_\d+$"
        ),

    )
)


expense_edit_handler = (
    CallbackQueryHandler(

        edit_expense_menu,

        pattern=(
            r"^expense_edit_\d+_\d+$"
        ),

    )
)


edit_field_handler = (
    CallbackQueryHandler(

        select_edit_field,

        pattern=(
            r"^edit_field_"
            r"(merchant|date|amount|category)$"
        ),

    )
)


edit_cancel_handler = (
    CallbackQueryHandler(

        cancel_edit_expense,

        pattern=(
            r"^edit_cancel_\d+$"
        ),

    )
)


delete_expense_confirmation_handler = (
    CallbackQueryHandler(

        delete_expense_confirmation,

        pattern=(
            r"^expense_delete_\d+_\d+$"
        ),

    )
)


delete_expense_handler = (
    CallbackQueryHandler(

        delete_expense,

        pattern=(
            r"^expense_confirm_delete_"
            r"\d+_\d+$"
        ),

    )
)


delete_expense_cancel_handler = (
    CallbackQueryHandler(

        cancel_delete_expense,

        pattern=(
            r"^expense_delete_cancel_\d+$"
        ),

    )
)