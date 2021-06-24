import re
from datetime import time
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram.ext import MessageHandler, Filters
from config import TOKEN

UPDATER = Updater(TOKEN)
# Get the dispatcher to register handlers
DISPATCHER = UPDATER.dispatcher
JOBS = UPDATER.job_queue


WELCOME_MSG = """
Привет! Я — бот-напоминатель про таблетки.
Напиши, когда тебе надо принимать таблетки, и я не отстану, пока ты не ответишь, что выпила их.

Список команд:
/help — получить это сообщение
/add_reminder — добавить новое ежедневное напоминание

P.S. обращения по умолчанию в женском роде
"""
TIME_QUESTION = "Напиши время, когда надо напоминать о таблетках (например, 11:35):"
WRONG_FORMAT = "Я не понимаю такой формат :(\n\nЧтобы отказаться от установки напоминания, напиши \"отмена\""
REMINDING = "{}, ты выпила таблетки?"
AGREE_WORDS = ["да", "да, выпил", "да, выпила", "выпил", "выпила", "ага", "угу", "дя"]
CAT_WORDS = ["мяу", "мур", "я котик", "мурлык", "мя"]


RESPONSES = {
    'kitten_mews': 'Гладь-гладь!',
    'yes': 'Ура, {}, молодец!',
    'fallback': 'я ничего не понял -_-',
}
CONDITIONS = [
    (lambda text: text in AGREE_WORDS, 'yes'),
    (lambda text: text in CAT_WORDS, 'kitten_mews'),
]
USERS_STATE = {}


def start(update: Update, context: CallbackContext) -> None:
    """Sends explanation on how to use the bot."""
    update.message.reply_text(WELCOME_MSG)


def process_time_choice(message, context):
    if re.match('[0-2]\\d[:. ][0-5]\\d', message.text):
        hour, minutes = [int(d) for d in re.findall('[0-5]\\d', message.text)]
        context.bot.send_message(
            chat_id=message.from_user.id,
            text=f'Ставлю напоминание на {hour} часов, {minutes} минут.'
            )
        hour -= 3
        point = time(hour, minutes)
        job_name = str(message.from_user.id) + '_' + str(hour) + ':' + str(minutes)

        def remind(context: CallbackContext):
            context.bot.send_message(
                chat_id=message.from_user.id,
                text=REMINDING.format(message.from_user.first_name)
                )

        JOBS.run_daily(remind, point, days=(0, 1, 2, 3, 4, 5, 6),  name=job_name)
        USERS_STATE[message.from_user.id] = 'choosing_interval'
    else:
        context.bot.send_message(chat_id=message.from_user.id, text=WRONG_FORMAT)



def process_chitchat(message):
    for func, resp_type in CONDITIONS:
        if func(message.text):
            message.reply_text(
                RESPONSES[resp_type].format(message.from_user.first_name)
            )
            break
    else:
        message.reply_text(RESPONSES['fallback'])


def handle_message(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id in USERS_STATE:
        if USERS_STATE[update.message.from_user.id] == 'choosing_time':
            process_time_choice(update.message, context)
        elif USERS_STATE[update.message.from_user.id] == 'choosing_interval':
            pass
        else:
            process_chitchat(update.message)
    else:
        USERS_STATE[update.message.from_user.id] = 'blank'
        process_chitchat(update.message)


def adding_reminder(update: Update, context: CallbackContext):
    USERS_STATE[update.message.from_user.id] = 'choosing_time'
    context.bot.send_message(chat_id=update.message.from_user.id, text=TIME_QUESTION)


def main() -> None:
    """Run bot."""
    # on different commands - answer in Telegram
    DISPATCHER.add_handler(CommandHandler("start", start))
    DISPATCHER.add_handler(CommandHandler("help", start))
    DISPATCHER.add_handler(CommandHandler("add_reminder", adding_reminder))
    DISPATCHER.add_handler(MessageHandler(Filters.text, handle_message))

    # Start the Bot
    UPDATER.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    UPDATER.idle()

if __name__ == '__main__':
    main()