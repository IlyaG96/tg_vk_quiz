from telegram import ReplyKeyboardMarkup
from telegram.ext import (CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)
from environs import Env
from load_questions import generate_questions, chose_question
from redis_db import run_base, write_question_db, write_scores_db, read_question_db, read_scores_db
from compare_phrases import compare_phrases
from enum import Enum


class BotStates(Enum):
    ASK_QUESTION = 1
    CHECK_ANSWER = 2
    USER_CHOSE_ACTION = 3


def build_menu(buttons, columns,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[button:button + columns] for button in range(0, len(buttons), columns)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


def start(update, context):
    text = f'Привет! Я - бот, который может по достоинству оценить широкий кругозор и эрудированность. ' \
           'Я буду задавать тебе вопросы на разные темы, а ты пиши ответы. ' \
           'К сожалению, меня еще не до конца натренировали, поэтому я иногда ошибаюсь при проверке ответов.' \
           'Удачи!'
    buttons = ['Начать игру!']
    keyboard = build_menu(buttons, columns=1)

    update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
        )
    )

    return BotStates.ASK_QUESTION


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
    context.bot_data['question_num'] = question_num
    write_question_db(redis_base, user, question_num)

    buttons = ['Сдаться', 'Мой счет']
    keyboard = build_menu(buttons, columns=2)

    update.message.reply_text(
        question,
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
        )
    )

    return BotStates.CHECK_ANSWER


def check_answer(update, context):

    redis_base = context.bot_data['redis_base']
    user = update.message.chat_id
    correct_answer = context.bot_data['correct_answer']
    user_answer = update.message.text
    buttons = ['Новый вопрос!']
    keyboard = build_menu(buttons, columns=2)
    if compare_phrases(user_answer, correct_answer):

        score = int(read_scores_db(redis_base, user))
        score += 1
        if not score:
            score = 1
        question_num = int(context.bot_data['question_num'])
        question_num += 1
        write_scores_db(redis_base, user, score)
        write_question_db(redis_base, user, question_num)
        update.message.reply_text(
            f'Ура! Ответ правильный! Ваш Счет: {score}',
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
            )
        )
        return BotStates.USER_CHOSE_ACTION

    else:
        buttons = ['Попробовать еще раз!', 'Сдаться']
        keyboard = build_menu(buttons, columns=2)
        update.message.reply_text(
            f'Пока неверно. Попробуешь еще или сдаешься?',
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
            )
        )

        return BotStates.USER_CHOSE_ACTION


def draw(update, context):

    redis_base = context.bot_data['redis_base']
    user = update.message.chat_id
    question_num = int(context.bot_data['question_num'])
    question_num += 1
    write_question_db(redis_base, user, question_num)
    buttons = ['Ок']
    keyboard = build_menu(buttons, columns=1)
    update.message.reply_text(
        f'Хорошо, перехожу к следующему вопросу',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True
        )
    )

    return BotStates.ASK_QUESTION


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
            BotStates.ASK_QUESTION: [
                MessageHandler(Filters.text, ask_question),
                MessageHandler(Filters.regex('^Сдаться$'), ask_question),
            ],
            BotStates.CHECK_ANSWER: [
                MessageHandler(Filters.regex('^Сдаться$'), draw),
                MessageHandler(Filters.regex('^Попробовать еще раз!$'), ask_question),
                MessageHandler(Filters.text, check_answer)
            ],
            BotStates.USER_CHOSE_ACTION: [
                MessageHandler(Filters.regex('^Новый вопрос!$'), ask_question),
                MessageHandler(Filters.regex('^Попробовать еще раз!$'), ask_question),
                MessageHandler(Filters.regex('^Сдаться$'), draw),
            ]
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