from telegram import Update
from telegram.ext import ContextTypes


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "👋 Halo! Selamat datang di Expense Bot.\n\n"
        "Bot ini akan membantu kamu mencatat pengeluaran harian.\n\n"
        "Fitur yang akan tersedia:\n"
        "💰 Catat pengeluaran\n"
        "📷 Scan struk\n"
        "📊 Rekap pengeluaran\n\n"
        "Untuk sekarang, bot sudah siap digunakan."
    )