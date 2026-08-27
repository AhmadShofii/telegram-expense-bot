from telegram import Update
from telegram.ext import ContextTypes


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message:
        return

    await update.message.reply_text(
        "👋 Halo! Selamat datang di Expense Bot.\n\n"
        "Bot ini membantu kamu mencatat "
        "pengeluaran harian.\n\n"
        "💰 Catat pengeluaran\n"
        "📊 Lihat laporan harian\n"
        "📅 Lihat laporan bulanan\n"
        "📈 Lihat rekap pengeluaran\n"
        "📷 Scan struk\n\n"
        "Contoh pencatatan:\n"
        "Makan siang 25000\n"
        "Bensin 50 ribu\n\n"
        "Kamu juga bisa langsung kirim "
        "foto struk."
    )