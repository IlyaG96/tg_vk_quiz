from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)
from environs import Env
from load_questions import generate_questions, chose_question
from compare_phrases import compare_phrases
from enum import Enum
import redis


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

    update.message.reply_text(
        'Мое дело предложить, твое - отказаться'
        ' Будет скучно - пиши.',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def ask_question(update, context):

    user = update.message.chat_id
    questions = context.bot_data['questions']
    redis_base = context.bot_data['redis_base']
    question_num = redis_base.hget(user, 'question_num')

    if not question_num:
        question_num = 1

    question, answer = chose_question(questions, question_num)
    context.user_data['correct_answer'] = answer
    context.user_data['question'] = question
    context.user_data['question_num'] = question_num

    redis_base.hset(user, 'question_num', question_num)

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
    correct_answer = context.user_data['correct_answer']
    user_answer = update.message.text

    buttons = ['Новый вопрос!']
    keyboard = build_menu(buttons, columns=2)

    if compare_phrases(user_answer, correct_answer):

        score = redis_base.hget(user, 'scores')
        if not score:
            score = 0
        score = int(score) + 1
        question_num = int(context.user_data['question_num'])
        question_num += 1
        redis_base.hset(user, 'scores', score)
        redis_base.hset(user, 'question_num', question_num)
        update.message.reply_text(
            f'Ура! Ответ правильный! Твой счет: {score}',
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
            'Пока неверно. Попробуешь еще или сдаешься?',
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
            )
        )

        return BotStates.USER_CHOSE_ACTION


def draw(update, context):

    correct_answer = context.user_data['correct_answer']
    redis_base = context.bot_data['redis_base']
    user = update.message.chat_id
    question_num = int(context.user_data['question_num'])
    question_num += 1
    redis_base.hset(user, 'question_num', question_num)

    buttons = ['Ок']
    keyboard = build_menu(buttons, columns=1)

    update.message.reply_text(
        f'Правильный ответ: {correct_answer}',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True
        )
    )

    return BotStates.ASK_QUESTION


def view_score(update, context):

    user = update.message.chat_id
    redis_base = context.bot_data['redis_base']
    score = redis_base.hget(user, 'scores')
    question = context.user_data['question']

    if not score:
        score = 0

    buttons = ['Сдаться', 'Мой счет']
    keyboard = build_menu(buttons, columns=2)

    context.bot.send_message(
        chat_id=user,
        text=f'Твой счет: {score} очков'
    )

    update.message.reply_text(
        question,
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
        )
    )

    return BotStates.CHECK_ANSWER


def main():
    env = Env()
    env.read_env()
    telegram_token = env.str('TELEGRAM_TOKEN')
    redis_host = env.str('REDIS_HOST')
    redis_port = env.str('REDIS_PORT')
    redis_password = env.str('REDIS_PASSWORD')
    updater = Updater(telegram_token, use_context=True)
    questions = generate_questions()

    redis_base = redis.Redis(host=redis_host,
                             port=redis_port,
                             password=redis_password,
                             decode_responses=True)

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
                MessageHandler(Filters.regex('^Мой счет$'), view_score),
                MessageHandler(Filters.text, check_answer)
            ],
            BotStates.USER_CHOSE_ACTION: [
                MessageHandler(Filters.regex('^Новый вопрос!$'), ask_question),
                MessageHandler(Filters.regex('^Попробовать еще раз!$'), ask_question),
                MessageHandler(Filters.regex('^Сдаться$'), draw),
                MessageHandler(Filters.text, check_answer)
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
