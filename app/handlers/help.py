from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
)


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

Contoh:

`Makan siang 25000`

📷 Kirim foto struk
untuk menggunakan OCR dan
membaca data transaksi secara otomatis.

━━━━━━━━━━━━━━━━━━━━

📋 *RIWAYAT*

/riwayat

Melihat daftar pengeluaran
yang sudah tersimpan.

Dari riwayat kamu dapat melihat
detail, mengedit, atau menghapus
transaksi.

━━━━━━━━━━━━━━━━━━━━

📊 *LAPORAN*

/hari

Melihat laporan pengeluaran
hari ini.

/tanggal

Melihat laporan berdasarkan
tanggal.

/bulan

Melihat laporan pengeluaran
bulan ini.

/rekap

Melihat rekap pengeluaran
bulan berjalan.

━━━━━━━━━━━━━━━━━━━━

💵 *BUDGET*

/budget

Melihat dan mengelola budget
bulan berjalan.

Bot juga akan memberikan
peringatan ketika penggunaan
budget mendekati atau melewati
batas yang ditentukan.

━━━━━━━━━━━━━━━━━━━━

📈 *STATISTIK*

/statistik

Melihat statistik pengeluaran
berdasarkan kategori.

Statistik dapat menampilkan:

• Total pengeluaran
• Pengeluaran berdasarkan kategori
• Persentase kategori
• Rata-rata pengeluaran

Tekan tombol
📈 *Lihat Grafik* untuk melihat
grafik pengeluaran.

━━━━━━━━━━━━━━━━━━━━

📤 *EXPORT*

/export

Mengexport laporan pengeluaran
bulan berjalan dalam format CSV.

File dapat dibuka menggunakan
Microsoft Excel atau aplikasi
spreadsheet lainnya.

━━━━━━━━━━━━━━━━━━━━

🔔 *DAILY REMINDER*

/reminder

Mengatur pengingat pencatatan
pengeluaran setiap hari.

Tersedia pilihan waktu:

• 07:00
• 08:00
• 09:00
• 12:00
• 18:00
• 19:00
• 20:00
• 21:00

Reminder dapat:

⏰ Diaktifkan
📋 Dilihat statusnya
🔕 Dimatikan

━━━━━━━━━━━━━━━━━━━━

ℹ️ *LAINNYA*

/start

Memulai bot.

/menu

Menampilkan menu utama.

/bantuan

Menampilkan panduan penggunaan.

━━━━━━━━━━━━━━━━━━━━

💡 *TIPS*

• Catat pengeluaran segera setelah transaksi.
• Gunakan foto struk untuk pencatatan otomatis.
• Gunakan /budget untuk mengontrol pengeluaran.
• Gunakan /statistik untuk melihat pola pengeluaran.
• Gunakan /export untuk menyimpan laporan.
• Aktifkan /reminder agar tidak lupa mencatat.
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

        [
            InlineKeyboardButton(
                "🔔 Reminder",
                callback_data="help_reminder",
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

        reply_markup=(
            build_help_keyboard()
        ),

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

        reply_markup=(
            build_help_keyboard()
        ),

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

            "/budget\n\n"

            "Melihat dan mengelola budget "
            "bulan berjalan.\n\n"

            "Budget dapat digunakan untuk "
            "mengontrol jumlah pengeluaran "
            "selama satu bulan.\n\n"

            "Bot juga dapat memberikan "
            "peringatan ketika penggunaan "
            "budget mendekati atau melewati "
            "batas.",

            parse_mode="Markdown",

        )

        return

    # ========================================================
    # STATISTICS
    # ========================================================

    if query.data == "help_statistics":

        await query.message.reply_text(

            "📈 *STATISTIK*\n\n"

            "/statistik\n\n"

            "Melihat statistik pengeluaran "
            "berdasarkan kategori.\n\n"

            "Informasi yang tersedia:\n"

            "• Total pengeluaran\n"
            "• Kategori pengeluaran\n"
            "• Persentase kategori\n"
            "• Rata-rata pengeluaran\n\n"

            "Tekan tombol 📈 *Lihat Grafik* "
            "untuk melihat grafik pengeluaran.",

            parse_mode="Markdown",

        )

        return

    # ========================================================
    # HISTORY
    # ========================================================

    if query.data == "help_history":

        await query.message.reply_text(

            "📋 *RIWAYAT*\n\n"

            "/riwayat\n\n"

            "Melihat daftar transaksi "
            "yang sudah tersimpan.\n\n"

            "Dari riwayat kamu dapat:\n\n"

            "• Melihat detail transaksi\n"
            "• Mengedit transaksi\n"
            "• Menghapus transaksi",

            parse_mode="Markdown",

        )

        return

    # ========================================================
    # EXPORT
    # ========================================================

    if query.data == "help_export":

        await query.message.reply_text(

            "📤 *EXPORT*\n\n"

            "/export\n\n"

            "Membuat laporan pengeluaran "
            "bulan berjalan dalam format CSV.\n\n"

            "File dapat dibuka menggunakan:\n\n"

            "• Microsoft Excel\n"
            "• Google Sheets\n"
            "• Aplikasi spreadsheet lainnya",

            parse_mode="Markdown",

        )

        return

    # ========================================================
    # REMINDER
    # ========================================================

    if query.data == "help_reminder":

        await query.message.reply_text(

            "🔔 *DAILY REMINDER*\n\n"

            "/reminder\n\n"

            "Mengatur pengingat pencatatan "
            "pengeluaran setiap hari.\n\n"

            "Pilihan waktu:\n\n"

            "• 07:00\n"
            "• 08:00\n"
            "• 09:00\n"
            "• 12:00\n"
            "• 18:00\n"
            "• 19:00\n"
            "• 20:00\n"
            "• 21:00\n\n"

            "Reminder dapat:\n\n"

            "⏰ Diaktifkan\n"
            "📋 Dilihat statusnya\n"
            "🔕 Dimatikan",

            parse_mode="Markdown",

        )

        return


# ============================================================
# CALLBACK HANDLER
# ============================================================

help_callback_handler = CallbackQueryHandler(

    help_callback,

    pattern=r"^help_",

)