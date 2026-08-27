from datetime import datetime, time

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
from database.models import Reminder


# ============================================================
# CONSTANT
# ============================================================

REMINDER_JOB_NAME = "daily_expense_reminder"


# ============================================================
# AVAILABLE REMINDER TIMES
# ============================================================

REMINDER_TIMES = {

    "07": (7, 0, "07:00"),

    "08": (8, 0, "08:00"),

    "09": (9, 0, "09:00"),

    "12": (12, 0, "12:00"),

    "18": (18, 0, "18:00"),

    "19": (19, 0, "19:00"),

    "20": (20, 0, "20:00"),

    "21": (21, 0, "21:00"),

}


# ============================================================
# REMINDER MESSAGE
# ============================================================

REMINDER_MESSAGE = (

    "🔔 *PENGINGAT PENGELUARAN*\n"
    "━━━━━━━━━━━━━━━━━━━━\n\n"

    "👋 Hai! Sudah mencatat "
    "pengeluaran hari ini?\n\n"

    "💰 Jangan lupa mencatat setiap "
    "transaksi agar laporan keuangan "
    "kamu tetap akurat.\n\n"

    "📝 *Catat manual*\n"
    "`Makan siang 25000`\n\n"

    "📷 *Atau kirim foto struk*\n"
    "Bot akan membantu membaca "
    "transaksi secara otomatis.\n\n"

    "━━━━━━━━━━━━━━━━━━━━\n\n"

    "💡 *Tips:* Catat pengeluaran "
    "segera setelah transaksi."

)


# ============================================================
# MAIN KEYBOARD
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
                "📋 Lihat Status",
                callback_data="reminder_status",
            ),

            InlineKeyboardButton(
                "🔕 Matikan",
                callback_data="reminder_off",
            ),

        ],

    ]

    return InlineKeyboardMarkup(
        keyboard
    )


# ============================================================
# TIME KEYBOARD
# ============================================================

def build_time_keyboard():

    keyboard = [

        [

            InlineKeyboardButton(
                "🌅 07:00",
                callback_data="reminder_time_07",
            ),

            InlineKeyboardButton(
                "☀️ 08:00",
                callback_data="reminder_time_08",
            ),

            InlineKeyboardButton(
                "☀️ 09:00",
                callback_data="reminder_time_09",
            ),

        ],

        [

            InlineKeyboardButton(
                "🍽️ 12:00",
                callback_data="reminder_time_12",
            ),

            InlineKeyboardButton(
                "🌆 18:00",
                callback_data="reminder_time_18",
            ),

            InlineKeyboardButton(
                "🌆 19:00",
                callback_data="reminder_time_19",
            ),

        ],

        [

            InlineKeyboardButton(
                "🌙 20:00",
                callback_data="reminder_time_20",
            ),

            InlineKeyboardButton(
                "🌙 21:00",
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
# GET REMINDER
# ============================================================

def get_reminder(
    user_id: int,
):

    db = SessionLocal()

    try:

        reminder = (

            db.query(Reminder)

            .filter(
                Reminder.user_id == user_id
            )

            .first()

        )

        if reminder is None:

            return None

        return {

            "id": reminder.id,

            "user_id": reminder.user_id,

            "enabled": reminder.enabled,

            "hour": reminder.hour,

            "minute": reminder.minute,

        }

    except Exception as error:

        print(
            "❌ Get reminder error:"
        )

        print(
            repr(error)
        )

        return None

    finally:

        db.close()


# ============================================================
# GET ACTIVE REMINDERS
# ============================================================

def get_active_reminders():

    db = SessionLocal()

    try:

        reminders = (

            db.query(Reminder)

            .filter(
                Reminder.enabled.is_(True)
            )

            .all()

        )

        result = []

        for reminder in reminders:

            result.append({

                "user_id": reminder.user_id,

                "hour": reminder.hour,

                "minute": reminder.minute,

            })

        return result

    except Exception as error:

        print(
            "❌ Get active reminders error:"
        )

        print(
            repr(error)
        )

        return []

    finally:

        db.close()


# ============================================================
# SAVE REMINDER
# ============================================================

def save_reminder(
    user_id: int,
    hour: int,
    minute: int,
):

    db = SessionLocal()

    try:

        reminder = (

            db.query(Reminder)

            .filter(
                Reminder.user_id == user_id
            )

            .first()

        )

        now = datetime.now()

        # ====================================================
        # CREATE
        # ====================================================

        if reminder is None:

            reminder = Reminder(

                user_id=user_id,

                enabled=True,

                hour=hour,

                minute=minute,

                created_at=now,

                updated_at=now,

            )

            db.add(
                reminder
            )

        # ====================================================
        # UPDATE
        # ====================================================

        else:

            reminder.enabled = True

            reminder.hour = hour

            reminder.minute = minute

            reminder.updated_at = now

        db.commit()

        db.refresh(
            reminder
        )

        return reminder

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


# ============================================================
# DISABLE REMINDER
# ============================================================

def disable_reminder(
    user_id: int,
):

    db = SessionLocal()

    try:

        reminder = (

            db.query(Reminder)

            .filter(
                Reminder.user_id == user_id
            )

            .first()

        )

        if reminder is not None:

            reminder.enabled = False

            reminder.updated_at = datetime.now()

            db.commit()

        return reminder

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


# ============================================================
# REMOVE OLD JOB
# ============================================================

def remove_reminder_job(
    user_id: int,
    context: ContextTypes.DEFAULT_TYPE,
):

    if context.job_queue is None:

        return

    job_name = (

        f"{REMINDER_JOB_NAME}_"
        f"{user_id}"

    )

    jobs = (

        context.job_queue

        .get_jobs_by_name(
            job_name
        )

    )

    for job in jobs:

        job.schedule_removal()


# ============================================================
# CREATE DAILY JOB
# ============================================================

def create_reminder_job(
    user_id: int,
    context: ContextTypes.DEFAULT_TYPE,
    hour: int,
    minute: int,
):

    if context.job_queue is None:

        return False

    # ========================================================
    # REMOVE OLD JOB
    # ========================================================

    remove_reminder_job(

        user_id,

        context,

    )

    # ========================================================
    # JOB NAME
    # ========================================================

    job_name = (

        f"{REMINDER_JOB_NAME}_"
        f"{user_id}"

    )

    # ========================================================
    # CREATE JOB
    # ========================================================

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

    return True


# ============================================================
# SEND REMINDER
# ============================================================

async def send_reminder(
    context: ContextTypes.DEFAULT_TYPE,
):

    job = context.job

    if job is None:

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

    # ========================================================
    # CHECK DATABASE
    # ========================================================

    reminder = get_reminder(
        user_id
    )

    if reminder is None:

        return

    if not reminder["enabled"]:

        return

    # ========================================================
    # SEND
    # ========================================================

    try:

        await context.bot.send_message(

            chat_id=user_id,

            text=REMINDER_MESSAGE,

            parse_mode="Markdown",

        )

        print(

            f"🔔 Reminder dikirim "
            f"ke user {user_id}"

        )

    except Exception as error:

        print(
            "❌ Reminder send error:"
        )

        print(
            repr(error)
        )


# ============================================================
# BUILD CURRENT STATUS
# ============================================================

def build_status_text(
    reminder,
) -> str:

    if (

        reminder is not None

        and reminder["enabled"]

    ):

        time_text = (

            f"{reminder['hour']:02d}:"
            f"{reminder['minute']:02d}"

        )

        return (

            "🟢 *AKTIF*\n\n"

            f"⏰ Waktu: *{time_text}*\n"

            "📅 Frekuensi: *Setiap hari*\n\n"

            "🔔 Reminder akan dikirim "
            "otomatis sesuai jadwal."

        )

    return (

        "🔴 *TIDAK AKTIF*\n\n"

        "Belum ada reminder aktif.\n\n"

        "Tekan ⏰ *Atur Reminder* "
        "untuk mengaktifkannya."

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

    user = update.effective_user

    if user is None:

        return

    reminder = get_reminder(
        user.id
    )

    message = (

        "🔔 *DAILY REMINDER*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "Atur pengingat agar kamu "
        "tidak lupa mencatat "
        "pengeluaran setiap hari.\n\n"

        "📋 *STATUS SAAT INI*\n\n"

        f"{build_status_text(reminder)}\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n\n"

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

    if query is None:

        return

    await query.answer()

    await query.edit_message_text(

        "⏰ *ATUR DAILY REMINDER*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "Pilih waktu yang paling nyaman "
        "untuk menerima pengingat.\n\n"

        "🌅 Pagi\n"
        "☀️ Siang\n"
        "🌆 Sore\n"
        "🌙 Malam\n\n"

        "Reminder akan dikirim "
        "*setiap hari* pada waktu "
        "yang kamu pilih.",

        reply_markup=(
            build_time_keyboard()
        ),

        parse_mode="Markdown",

    )


# ============================================================
# SELECT TIME
# ============================================================

async def reminder_time_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if query is None:

        return

    await query.answer()

    user = update.effective_user

    if user is None:

        return

    user_id = user.id

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

    if selected_time is None:

        await query.edit_message_text(

            "❌ *WAKTU TIDAK VALID*\n\n"

            "Silakan pilih waktu "
            "yang tersedia.",

            parse_mode="Markdown",

        )

        return

    hour = selected_time[0]

    minute = selected_time[1]

    time_text = selected_time[2]

    # ========================================================
    # CHECK JOB QUEUE
    # ========================================================

    if context.job_queue is None:

        await query.edit_message_text(

            "❌ *REMINDER TIDAK TERSEDIA*\n\n"

            "Job Queue Telegram belum "
            "tersedia pada environment ini.\n\n"

            "Install dependency:\n\n"

            "`python -m pip install "
            "\"python-telegram-bot[job-queue]\"`",

            parse_mode="Markdown",

        )

        return

    # ========================================================
    # SAVE DATABASE
    # ========================================================

    try:

        save_reminder(

            user_id=user_id,

            hour=hour,

            minute=minute,

        )

    except Exception as error:

        print(
            "❌ Reminder database error:"
        )

        print(
            repr(error)
        )

        await query.edit_message_text(

            "❌ *GAGAL MENYIMPAN*\n\n"

            "Pengaturan reminder "
            "tidak dapat disimpan.\n\n"

            "Silakan coba lagi.",

            parse_mode="Markdown",

        )

        return

    # ========================================================
    # CREATE JOB
    # ========================================================

    success = create_reminder_job(

        user_id=user_id,

        context=context,

        hour=hour,

        minute=minute,

    )

    if not success:

        await query.edit_message_text(

            "❌ *GAGAL MEMBUAT JADWAL*\n\n"

            "Reminder belum dapat "
            "diaktifkan.",

            parse_mode="Markdown",

        )

        return

    # ========================================================
    # SUCCESS
    # ========================================================

    await query.edit_message_text(

        "✅ *REMINDER BERHASIL DIATUR*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "🟢 Status: *Aktif*\n"

        f"⏰ Waktu: *{time_text}*\n"

        "📅 Frekuensi: *Setiap hari*\n\n"

        "💾 Pengaturan sudah tersimpan.\n\n"

        "🔄 Jika bot di-restart, "
        "reminder akan dipulihkan "
        "secara otomatis.",

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

    if query is None:

        return

    await query.answer()

    user = update.effective_user

    if user is None:

        return

    reminder = get_reminder(
        user.id
    )

    message = (

        "📋 *STATUS DAILY REMINDER*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"

        f"{build_status_text(reminder)}\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "Gunakan menu di bawah "
        "untuk mengubah pengaturan."

    )

    await query.edit_message_text(

        message,

        reply_markup=(
            build_reminder_keyboard()
        ),

        parse_mode="Markdown",

    )


# ============================================================
# DISABLE
# ============================================================

async def reminder_off_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if query is None:

        return

    await query.answer()

    user = update.effective_user

    if user is None:

        return

    user_id = user.id

    try:

        disable_reminder(
            user_id
        )

    except Exception as error:

        print(
            "❌ Reminder disable error:"
        )

        print(
            repr(error)
        )

        await query.edit_message_text(

            "❌ *GAGAL MEMATIKAN REMINDER*\n\n"

            "Terjadi kesalahan saat "
            "mengubah status reminder.",

            parse_mode="Markdown",

        )

        return

    # ========================================================
    # REMOVE JOB
    # ========================================================

    remove_reminder_job(

        user_id,

        context,

    )

    await query.edit_message_text(

        "🔕 *REMINDER DIMATIKAN*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "Reminder harian kamu "
        "sudah dinonaktifkan.\n\n"

        "💾 Pengaturan tetap tersimpan "
        "di database sehingga kamu "
        "bisa mengaktifkannya kembali "
        "kapan saja.",

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

    if query is None:

        return

    await query.answer()

    user = update.effective_user

    if user is None:

        return

    reminder = get_reminder(
        user.id
    )

    message = (

        "🔔 *DAILY REMINDER*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "Atur pengingat agar kamu "
        "tidak lupa mencatat "
        "pengeluaran setiap hari.\n\n"

        "📋 *STATUS SAAT INI*\n\n"

        f"{build_status_text(reminder)}\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "Pilih menu di bawah:"

    )

    await query.edit_message_text(

        message,

        reply_markup=(
            build_reminder_keyboard()
        ),

        parse_mode="Markdown",

    )


# ============================================================
# RESTORE REMINDERS AFTER RESTART
# ============================================================

def restore_reminders(
    application,
):

    job_queue = application.job_queue

    if job_queue is None:

        print(
            "⚠️ JobQueue tidak tersedia."
        )

        return

    # ========================================================
    # GET ACTIVE REMINDERS
    # ========================================================

    reminders = (
        get_active_reminders()
    )

    restored = 0

    # ========================================================
    # RESTORE EACH USER
    # ========================================================

    for reminder in reminders:

        user_id = (
            reminder["user_id"]
        )

        hour = (
            reminder["hour"]
        )

        minute = (
            reminder["minute"]
        )

        job_name = (

            f"{REMINDER_JOB_NAME}_"
            f"{user_id}"

        )

        # ====================================================
        # CHECK DUPLICATE
        # ====================================================

        existing_jobs = (

            job_queue

            .get_jobs_by_name(
                job_name
            )

        )

        if existing_jobs:

            continue

        # ====================================================
        # CREATE JOB
        # ====================================================

        job_queue.run_daily(

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

        restored += 1

    print(

        "🔄 Persistent reminder dipulihkan: "
        f"{restored} reminder."

    )


# ============================================================
# CALLBACK HANDLERS
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