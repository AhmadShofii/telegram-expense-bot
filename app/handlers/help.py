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
💰 *EXPENSE BOT*
━━━━━━━━━━━━━━━━━━━━

👋 *Kelola pengeluaranmu dengan mudah.*

Catat transaksi secara manual atau
gunakan foto struk untuk membantu
mencatat pengeluaran secara otomatis.

━━━━━━━━━━━━━━━━━━━━

📝 *CATAT PENGELUARAN*

Ketik langsung:

`Makan siang 25000`

atau:

`Bensin 50 ribu`

Setelah itu periksa data dan tekan
*✅ Simpan* untuk menyimpan transaksi.

📷 *SCAN STRUK*

Kirim foto struk dan bot akan mencoba
membaca informasi transaksi secara
otomatis menggunakan OCR.

━━━━━━━━━━━━━━━━━━━━

📊 *LAPORAN*

`/hari`
Melihat pengeluaran hari ini.

`/tanggal`
Melihat pengeluaran berdasarkan tanggal.

Contoh:

`/tanggal 27-08-2026`

`/bulan`
Melihat pengeluaran bulan berjalan.

`/rekap`
Melihat ringkasan pengeluaran
berdasarkan kategori.

━━━━━━━━━━━━━━━━━━━━

📋 *RIWAYAT*

`/riwayat`

Melihat transaksi yang sudah tersimpan.

Kamu juga dapat:

• 👁️ Melihat detail
• ✏️ Mengedit transaksi
• 🗑️ Menghapus transaksi

━━━━━━━━━━━━━━━━━━━━

💵 *BUDGET*

`/budget`

Mengatur dan melihat budget
pengeluaran bulan berjalan.

Bot juga dapat memberikan peringatan
ketika penggunaan budget mendekati
atau melewati batas.

━━━━━━━━━━━━━━━━━━━━

📈 *STATISTIK*

`/statistik`

Melihat analisis pengeluaran:

• 💸 Total pengeluaran
• 🏷️ Pengeluaran per kategori
• 📊 Persentase kategori
• 💰 Rata-rata pengeluaran
• 📈 Grafik pengeluaran

━━━━━━━━━━━━━━━━━━━━

📤 *EXPORT*

`/export`

Mengexport laporan pengeluaran
bulan berjalan dalam format CSV.

File dapat dibuka menggunakan:

• Microsoft Excel
• Google Sheets
• Aplikasi spreadsheet lainnya

━━━━━━━━━━━━━━━━━━━━

🔔 *DAILY REMINDER*

`/reminder`

Atur pengingat pencatatan pengeluaran
setiap hari.

Pilihan waktu:

• 🌅 07:00
• ☀️ 08:00
• ☀️ 09:00
• 🍽️ 12:00
• 🌆 18:00
• 🌆 19:00
• 🌙 20:00
• 🌙 21:00

Reminder dapat:

⏰ Diaktifkan
📋 Dilihat statusnya
🔕 Dimatikan

━━━━━━━━━━━━━━━━━━━━

🚀 *PERINTAH UTAMA*

`/start`
Memulai menggunakan bot.

`/menu`
Menampilkan menu utama.

`/bantuan`
Menampilkan panduan penggunaan.

━━━━━━━━━━━━━━━━━━━━

💡 *TIPS*

• Catat pengeluaran segera setelah transaksi.
• Gunakan foto struk untuk pencatatan otomatis.
• Gunakan `/budget` untuk mengontrol pengeluaran.
• Gunakan `/statistik` untuk melihat pola pengeluaran.
• Gunakan `/export` untuk menyimpan laporan.
• Aktifkan `/reminder` agar tidak lupa mencatat.

━━━━━━━━━━━━━━━━━━━━

✨ *Selamat mengelola keuangan!*
"""


# ============================================================
# HELP KEYBOARD
# ============================================================

def build_help_keyboard():

    keyboard = [

        [
            InlineKeyboardButton(
                "💵 Budget",
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

            "💵 *BUDGET*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"

            "`/budget`\n\n"

            "Atur batas pengeluaran "
            "untuk bulan berjalan.\n\n"

            "Dengan budget kamu dapat "
            "memantau penggunaan uang "
            "selama satu bulan.\n\n"

            "Bot akan memberikan peringatan "
            "ketika penggunaan budget "
            "mendekati atau melewati batas.\n\n"

            "💡 Cocok digunakan untuk "
            "mengontrol pengeluaran bulanan.",

            parse_mode="Markdown",

        )

        return

    # ========================================================
    # STATISTICS
    # ========================================================

    if query.data == "help_statistics":

        await query.message.reply_text(

            "📈 *STATISTIK*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"

            "`/statistik`\n\n"

            "Melihat analisis pengeluaran "
            "berdasarkan kategori.\n\n"

            "📊 Informasi yang tersedia:\n\n"

            "• 💸 Total pengeluaran\n"
            "• 🏷️ Pengeluaran berdasarkan kategori\n"
            "• 📊 Persentase kategori\n"
            "• 💰 Rata-rata pengeluaran\n"
            "• 📈 Grafik pengeluaran\n\n"

            "Gunakan fitur ini untuk melihat "
            "pola pengeluaran kamu dengan "
            "lebih mudah.",

            parse_mode="Markdown",

        )

        return

    # ========================================================
    # HISTORY
    # ========================================================

    if query.data == "help_history":

        await query.message.reply_text(

            "📋 *RIWAYAT PENGELUARAN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"

            "`/riwayat`\n\n"

            "Melihat transaksi pengeluaran "
            "yang sudah tersimpan.\n\n"

            "Dari riwayat kamu dapat:\n\n"

            "• 👁️ Melihat detail transaksi\n"
            "• ✏️ Mengedit transaksi\n"
            "• 🗑️ Menghapus transaksi\n\n"

            "💡 Gunakan riwayat untuk "
            "memeriksa kembali transaksi "
            "yang sudah dicatat.",

            parse_mode="Markdown",

        )

        return

    # ========================================================
    # EXPORT
    # ========================================================

    if query.data == "help_export":

        await query.message.reply_text(

            "📤 *EXPORT LAPORAN*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"

            "`/export`\n\n"

            "Menghasilkan laporan pengeluaran "
            "bulan berjalan dalam format CSV.\n\n"

            "📄 File dapat dibuka menggunakan:\n\n"

            "• Microsoft Excel\n"
            "• Google Sheets\n"
            "• Aplikasi spreadsheet lainnya\n\n"

            "💡 Cocok untuk menyimpan atau "
            "mengolah data pengeluaran "
            "di luar Telegram.",

            parse_mode="Markdown",

        )

        return

    # ========================================================
    # REMINDER
    # ========================================================

    if query.data == "help_reminder":

        await query.message.reply_text(

            "🔔 *DAILY REMINDER*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"

            "`/reminder`\n\n"

            "Atur pengingat agar kamu "
            "tidak lupa mencatat "
            "pengeluaran setiap hari.\n\n"

            "⏰ Pilihan waktu:\n\n"

            "• 🌅 07:00\n"
            "• ☀️ 08:00\n"
            "• ☀️ 09:00\n"
            "• 🍽️ 12:00\n"
            "• 🌆 18:00\n"
            "• 🌆 19:00\n"
            "• 🌙 20:00\n"
            "• 🌙 21:00\n\n"

            "Reminder dapat:\n\n"

            "🟢 Diaktifkan\n"
            "📋 Dilihat statusnya\n"
            "🔕 Dimatikan\n\n"

            "💡 Pengaturan reminder akan "
            "tetap tersimpan meskipun bot "
            "di-restart.",

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