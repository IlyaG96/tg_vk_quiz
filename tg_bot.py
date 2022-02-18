from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)
from environs import Env


def build_menu(buttons, n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


def start(update, context):
    text = 'Добро пожаловать в Джуманджи!'
    buttons = ['Начать игру!']
    keyboard = build_menu(buttons, n_cols=1)

    update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
        )
    )

    return 'ask_question'


def cancel(update, context):
    pass


def ask_question(update, context):
    text = 'Поехали?'
    buttons = ['Новый вопрос!', 'Сдаться', 'Мой счет']
    keyboard = build_menu(buttons, n_cols=2)

    update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
        )
    )

    return 'ask_question'


def main():
    env = Env()
    env.read_env()
    TELEGRAM_TOKEN = env.str('TELEGRAM_TOKEN')
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    start_quiz = ConversationHandler(
        entry_points=[
            CommandHandler('start', start)
        ],
        states={
            'ask_question': [
                MessageHandler(
                    Filters.text,
                    ask_question,
                    pass_user_data=True
                )
            ],
        },
        per_user=True,
        per_chat=True,
        fallbacks=[
            CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(start_quiz)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()