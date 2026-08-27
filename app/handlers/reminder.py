from datetime import time

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
# CONSTANT
# ============================================================

REMINDER_JOB_NAME = "daily_expense_reminder"


# ============================================================
# REMINDER TIMES
# ============================================================

REMINDER_TIMES = {
    "07": (
        7,
        0,
        "07:00",
    ),

    "08": (
        8,
        0,
        "08:00",
    ),

    "09": (
        9,
        0,
        "09:00",
    ),

    "12": (
        12,
        0,
        "12:00",
    ),

    "18": (
        18,
        0,
        "18:00",
    ),

    "19": (
        19,
        0,
        "19:00",
    ),

    "20": (
        20,
        0,
        "20:00",
    ),

    "21": (
        21,
        0,
        "21:00",
    ),
}


# ============================================================
# REMINDER MESSAGE
# ============================================================

REMINDER_MESSAGE = (
    "🔔 *Pengingat Pengeluaran*\n\n"
    "Sudah mencatat pengeluaran hari ini? 💰\n\n"
    "Jangan lupa catat transaksi kamu "
    "agar laporan dan statistik tetap akurat.\n\n"
    "📝 Contoh:\n"
    "`Makan siang 25000`\n\n"
    "📷 Atau kirim foto struk "
    "untuk pencatatan otomatis."
)


# ============================================================
# REMINDER MENU
# ============================================================

def build_reminder_keyboard():

    keyboard = [

        [
            InlineKeyboardButton(
                "⏰ Atur Reminder",
                callback_data="reminder_set",
            ),
        ],

        [
            InlineKeyboardButton(
                "📋 Status Reminder",
                callback_data="reminder_status",
            ),

            InlineKeyboardButton(
                "🔕 Matikan Reminder",
                callback_data="reminder_off",
            ),
        ],

    ]

    return InlineKeyboardMarkup(
        keyboard
    )


# ============================================================
# TIME MENU
# ============================================================

def build_time_keyboard():

    keyboard = [

        [
            InlineKeyboardButton(
                "07:00",
                callback_data="reminder_time_07",
            ),

            InlineKeyboardButton(
                "08:00",
                callback_data="reminder_time_08",
            ),

            InlineKeyboardButton(
                "09:00",
                callback_data="reminder_time_09",
            ),
        ],

        [
            InlineKeyboardButton(
                "12:00",
                callback_data="reminder_time_12",
            ),

            InlineKeyboardButton(
                "18:00",
                callback_data="reminder_time_18",
            ),

            InlineKeyboardButton(
                "19:00",
                callback_data="reminder_time_19",
            ),
        ],

        [
            InlineKeyboardButton(
                "20:00",
                callback_data="reminder_time_20",
            ),

            InlineKeyboardButton(
                "21:00",
                callback_data="reminder_time_21",
            ),
        ],

        [
            InlineKeyboardButton(
                "⬅️ Kembali",
                callback_data="reminder_back",
            ),
        ],

    ]

    return InlineKeyboardMarkup(
        keyboard
    )


# ============================================================
# /REMINDER
# ============================================================

async def reminder_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:

        return

    enabled = context.user_data.get(
        "reminder_enabled",
        False,
    )

    reminder_time = context.user_data.get(
        "reminder_time",
    )

    if enabled and reminder_time:

        status_text = (
            f"🟢 Aktif\n"
            f"⏰ Setiap hari pukul "
            f"*{reminder_time}*"
        )

    else:

        status_text = (
            "🔴 Tidak aktif"
        )

    message = (

        "🔔 *DAILY REMINDER*\n\n"

        "Reminder akan mengingatkan kamu "
        "untuk mencatat pengeluaran setiap hari.\n\n"

        f"Status saat ini:\n"
        f"{status_text}\n\n"

        "Pilih menu di bawah:"

    )

    await update.message.reply_text(

        message,

        reply_markup=(
            build_reminder_keyboard()
        ),

        parse_mode="Markdown",

    )


# ============================================================
# SET REMINDER
# ============================================================

async def reminder_set_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:

        return

    await query.answer()

    await query.edit_message_text(

        "⏰ *Atur Daily Reminder*\n\n"

        "Pilih waktu reminder yang kamu inginkan.\n\n"

        "Reminder akan dikirim setiap hari "
        "pada waktu yang dipilih.",

        reply_markup=(
            build_time_keyboard()
        ),

        parse_mode="Markdown",

    )


# ============================================================
# CREATE JOB
# ============================================================

def create_reminder_job(
    user_id: int,
    context: ContextTypes.DEFAULT_TYPE,
    hour: int,
    minute: int,
):

    # ========================================================
    # REMOVE EXISTING JOB
    # ========================================================

    remove_reminder_job(
        user_id,
        context,
    )

    # ========================================================
    # CREATE DAILY JOB
    # ========================================================

    job_name = (
        f"{REMINDER_JOB_NAME}_{user_id}"
    )

    context.job_queue.run_daily(

        callback=send_reminder,

        time=time(
            hour=hour,
            minute=minute,
        ),

        chat_id=user_id,

        name=job_name,

        data={
            "user_id": user_id,
        },

    )


# ============================================================
# REMOVE JOB
# ============================================================

def remove_reminder_job(
    user_id: int,
    context: ContextTypes.DEFAULT_TYPE,
):

    if context.job_queue is None:

        return

    job_name = (
        f"{REMINDER_JOB_NAME}_{user_id}"
    )

    jobs = (
        context.job_queue.get_jobs_by_name(
            job_name
        )
    )

    for job in jobs:

        job.schedule_removal()


# ============================================================
# SEND REMINDER
# ============================================================

async def send_reminder(
    context: ContextTypes.DEFAULT_TYPE,
):

    job = context.job

    if not job:

        return

    user_id = None

    if job.data:

        user_id = job.data.get(
            "user_id"
        )

    if not user_id:

        user_id = job.chat_id

    if not user_id:

        return

    try:

        await context.bot.send_message(

            chat_id=user_id,

            text=REMINDER_MESSAGE,

            parse_mode="Markdown",

        )

    except Exception as error:

        print(
            "Reminder send error:"
        )

        print(
            repr(error)
        )


# ============================================================
# SELECT TIME
# ============================================================

async def reminder_time_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:

        return

    await query.answer()

    user = update.effective_user

    if not user:

        return

    user_id = user.id

    # ========================================================
    # GET SELECTED TIME
    # ========================================================

    prefix = "reminder_time_"

    if not query.data.startswith(
        prefix
    ):

        return

    time_key = query.data[
        len(prefix):
    ]

    selected_time = (
        REMINDER_TIMES.get(
            time_key
        )
    )

    if not selected_time:

        await query.edit_message_text(

            "❌ Waktu reminder tidak valid."

        )

        return

    hour = selected_time[0]

    minute = selected_time[1]

    time_text = selected_time[2]

    # ========================================================
    # CHECK JOBQUEUE
    # ========================================================

    if context.job_queue is None:

        await query.edit_message_text(

            "❌ Daily Reminder belum tersedia.\n\n"

            "Pastikan dependency berikut sudah "
            "terinstall:\n\n"

            "`python -m pip install "
            "\"python-telegram-bot[job-queue]\"`",

            parse_mode="Markdown",

        )

        return

    # ========================================================
    # CREATE JOB
    # ========================================================

    create_reminder_job(

        user_id,

        context,

        hour,

        minute,

    )

    # ========================================================
    # SAVE USER STATE
    # ========================================================

    context.user_data[
        "reminder_enabled"
    ] = True

    context.user_data[
        "reminder_time"
    ] = time_text

    context.user_data[
        "reminder_hour"
    ] = hour

    context.user_data[
        "reminder_minute"
    ] = minute

    # ========================================================
    # RESPONSE
    # ========================================================

    await query.edit_message_text(

        "✅ *Reminder berhasil diatur!*\n\n"

        f"🔔 Status: *Aktif*\n"
        f"⏰ Waktu: *{time_text}*\n"
        f"📅 Frekuensi: Setiap hari\n\n"

        "Bot akan mengingatkan kamu "
        "setiap hari pada waktu tersebut.",

        reply_markup=(
            build_reminder_keyboard()
        ),

        parse_mode="Markdown",

    )


# ============================================================
# STATUS
# ============================================================

async def reminder_status_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:

        return

    await query.answer()

    enabled = context.user_data.get(
        "reminder_enabled",
        False,
    )

    reminder_time = context.user_data.get(
        "reminder_time"
    )

    if enabled and reminder_time:

        message = (

            "📋 *STATUS DAILY REMINDER*\n\n"

            "🟢 Status: *Aktif*\n"

            f"⏰ Waktu: *{reminder_time}*\n"

            "📅 Frekuensi: Setiap hari"

        )

    else:

        message = (

            "📋 *STATUS DAILY REMINDER*\n\n"

            "🔴 Status: *Tidak aktif*\n\n"

            "Gunakan tombol "
            "⏰ *Atur Reminder* "
            "untuk mengaktifkan."

        )

    await query.edit_message_text(

        message,

        reply_markup=(
            build_reminder_keyboard()
        ),

        parse_mode="Markdown",

    )


# ============================================================
# TURN OFF
# ============================================================

async def reminder_off_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:

        return

    await query.answer()

    user = update.effective_user

    if not user:

        return

    user_id = user.id

    # ========================================================
    # REMOVE JOB
    # ========================================================

    remove_reminder_job(
        user_id,
        context,
    )

    # ========================================================
    # CLEAR STATE
    # ========================================================

    context.user_data.pop(
        "reminder_enabled",
        None,
    )

    context.user_data.pop(
        "reminder_time",
        None,
    )

    context.user_data.pop(
        "reminder_hour",
        None,
    )

    context.user_data.pop(
        "reminder_minute",
        None,
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    await query.edit_message_text(

        "🔕 *Reminder dimatikan.*\n\n"

        "Bot tidak akan lagi mengirim "
        "pengingat pengeluaran harian.",

        reply_markup=(
            build_reminder_keyboard()
        ),

        parse_mode="Markdown",

    )


# ============================================================
# BACK
# ============================================================

async def reminder_back_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:

        return

    await query.answer()

    enabled = context.user_data.get(
        "reminder_enabled",
        False,
    )

    reminder_time = context.user_data.get(
        "reminder_time"
    )

    if enabled and reminder_time:

        status_text = (
            f"🟢 Aktif\n"
            f"⏰ Setiap hari pukul "
            f"*{reminder_time}*"
        )

    else:

        status_text = (
            "🔴 Tidak aktif"
        )

    await query.edit_message_text(

        "🔔 *DAILY REMINDER*\n\n"

        "Reminder akan mengingatkan kamu "
        "untuk mencatat pengeluaran setiap hari.\n\n"

        f"Status saat ini:\n"
        f"{status_text}\n\n"

        "Pilih menu di bawah:",

        reply_markup=(
            build_reminder_keyboard()
        ),

        parse_mode="Markdown",

    )


# ============================================================
# CALLBACK HANDLER
# ============================================================

reminder_handler = CallbackQueryHandler(

    reminder_set_callback,

    pattern=r"^reminder_set$",

)


reminder_time_handler = CallbackQueryHandler(

    reminder_time_callback,

    pattern=r"^reminder_time_\d+$",

)


reminder_status_handler = CallbackQueryHandler(

    reminder_status_callback,

    pattern=r"^reminder_status$",

)


reminder_off_handler = CallbackQueryHandler(

    reminder_off_callback,

    pattern=r"^reminder_off$",

)


reminder_back_handler = CallbackQueryHandler(

    reminder_back_callback,

    pattern=r"^reminder_back$",

)