from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import ContextTypes


# ============================================================
# HELP MESSAGE
# ============================================================

HELP_MESSAGE = """
📊 *EXPENSE BOT*

Bot untuk mencatat dan mengelola
pengeluaran kamu dengan mudah.

━━━━━━━━━━━━━━━━━━━━

📌 *CARA PAKAI*

1️⃣ Kirim foto struk untuk membaca
   data transaksi secara otomatis.

2️⃣ Atau ketik pengeluaran manual,
   contoh:

   `Makan siang 25000`
   `Bensin 50 ribu`

3️⃣ Konfirmasi transaksi sebelum
   disimpan.

━━━━━━━━━━━━━━━━━━━━

💰 *PENCATATAN*

📝 Kirim teks pengeluaran
untuk mencatat transaksi manual.

📷 Kirim foto struk
untuk menggunakan OCR.

━━━━━━━━━━━━━━━━━━━━

📋 *RIWAYAT*

/riwayat
Melihat daftar pengeluaran.

━━━━━━━━━━━━━━━━━━━━

📊 *LAPORAN*

/hari
Laporan pengeluaran hari ini.

/tanggal
Laporan berdasarkan tanggal.

/bulan
Laporan pengeluaran bulan ini.

/rekap
Rekap pengeluaran bulan ini.

━━━━━━━━━━━━━━━━━━━━

💵 *BUDGET*

/budget
Melihat dan mengelola budget
bulan berjalan.

━━━━━━━━━━━━━━━━━━━━

📈 *STATISTIK*

/statistik
Melihat statistik pengeluaran
berdasarkan kategori.

/statistik
Kemudian tekan tombol
📈 *Lihat Grafik* untuk melihat
grafik pengeluaran.

━━━━━━━━━━━━━━━━━━━━

📤 *EXPORT*

/export
Export laporan pengeluaran
bulan berjalan dalam format CSV.

━━━━━━━━━━━━━━━━━━━━

ℹ️ *LAINNYA*

/start
Memulai bot.

/menu
Menampilkan menu bantuan.

/bantuan
Menampilkan panduan penggunaan.

━━━━━━━━━━━━━━━━━━━━

💡 *Tips*

• Catat pengeluaran segera setelah transaksi.
• Gunakan foto struk untuk pencatatan otomatis.
• Gunakan /statistik untuk melihat pola pengeluaran.
• Gunakan /export untuk menyimpan laporan.
"""


# ============================================================
# HELP KEYBOARD
# ============================================================

def build_help_keyboard():

    keyboard = [

        [
            InlineKeyboardButton(
                "💰 Budget",
                callback_data="help_budget",
            ),
            InlineKeyboardButton(
                "📈 Statistik",
                callback_data="help_statistics",
            ),
        ],

        [
            InlineKeyboardButton(
                "📋 Riwayat",
                callback_data="help_history",
            ),
            InlineKeyboardButton(
                "📤 Export",
                callback_data="help_export",
            ),
        ],

    ]

    return InlineKeyboardMarkup(
        keyboard
    )


# ============================================================
# /MENU
# ============================================================

async def menu_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:

        return

    await update.message.reply_text(

        HELP_MESSAGE,

        reply_markup=build_help_keyboard(),

        parse_mode="Markdown",

    )


# ============================================================
# /BANTUAN
# ============================================================

async def bantuan_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:

        return

    await update.message.reply_text(

        HELP_MESSAGE,

        reply_markup=build_help_keyboard(),

        parse_mode="Markdown",

    )


# ============================================================
# HELP CALLBACK
# ============================================================

async def help_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:

        return

    await query.answer()

    # ========================================================
    # BUDGET
    # ========================================================

    if query.data == "help_budget":

        await query.message.reply_text(

            "💵 *BUDGET*\n\n"

            "/budget\n"
            "Melihat budget bulan berjalan.\n\n"

            "Gunakan menu budget untuk "
            "mengatur atau mengedit budget.",

            parse_mode="Markdown",

        )

        return

    # ========================================================
    # STATISTICS
    # ========================================================

    if query.data == "help_statistics":

        await query.message.reply_text(

            "📈 *STATISTIK*\n\n"

            "/statistik\n"
            "Melihat total pengeluaran, "
            "kategori, persentase, dan "
            "rata-rata pengeluaran.\n\n"

            "Tekan tombol 📈 *Lihat Grafik* "
            "untuk melihat grafik kategori.",

            parse_mode="Markdown",

        )

        return

    # ========================================================
    # HISTORY
    # ========================================================

    if query.data == "help_history":

        await query.message.reply_text(

            "📋 *RIWAYAT*\n\n"

            "/riwayat\n"
            "Melihat daftar transaksi "
            "yang sudah tersimpan.\n\n"

            "Dari riwayat kamu dapat melihat "
            "detail, mengedit, atau menghapus "
            "transaksi.",

            parse_mode="Markdown",

        )

        return

    # ========================================================
    # EXPORT
    # ========================================================

    if query.data == "help_export":

        await query.message.reply_text(

            "📤 *EXPORT*\n\n"

            "/export\n"
            "Membuat laporan pengeluaran "
            "bulan berjalan dalam format CSV.\n\n"

            "File dapat dibuka menggunakan "
            "Microsoft Excel atau aplikasi "
            "spreadsheet lainnya.",

            parse_mode="Markdown",

        )

        return


# ============================================================
# CALLBACK HANDLER
# ============================================================

from telegram.ext import CallbackQueryHandler


help_callback_handler = (
    CallbackQueryHandler(

        help_callback,

        pattern=r"^help_",

    )
)