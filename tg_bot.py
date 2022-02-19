from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)
from environs import Env
from load_questions import generate_questions, chose_question
from redis_db import run_base, write_question_db, write_scores_db, read_question_db, read_scores_db
from compare_phrases import compare_phrases

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

    user = update.message.chat_id

    redis_base = context.bot_data['redis_base']
    question_num = read_question_db(redis_base, user)
    if not question_num:
        question_num = 1
    questions = context.bot_data['questions']
    question, answer = chose_question(questions, question_num)
    context.bot_data['correct_answer'] = answer
    write_question_db(redis_base, user, question_num)

    buttons = ['Новый вопрос!', 'Сдаться', 'Мой счет']
    keyboard = build_menu(buttons, n_cols=2)

    update.message.reply_text(
        question,
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
        )
    )

    return 'check_answer'


def check_answer(update, context):

    correct_answer = context.bot_data['correct_answer']
    user_answer = update.message.text
    if compare_phrases(user_answer, correct_answer):
        print('win')



def main():
    env = Env()
    env.read_env()
    TELEGRAM_TOKEN = env.str('TELEGRAM_TOKEN')
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    questions = generate_questions()
    redis_base = run_base()
    dispatcher = updater.dispatcher
    dispatcher.bot_data['questions'] = questions
    dispatcher.bot_data['redis_base'] = redis_base

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
            'check_answer': [
                MessageHandler(
                    Filters.text,
                    check_answer,
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