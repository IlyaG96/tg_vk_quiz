from redis_db import run_base, write_question_db, write_scores_db, read_question_db, read_scores_db
from load_questions import generate_questions, chose_question
from compare_phrases import compare_phrases
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from environs import Env
import vk_api


def default_keyboard():

    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Вопрос', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.PRIMARY)

    return keyboard


def keyboard_without_draw():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Вопрос', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.PRIMARY)

    return keyboard


def main(vk_token):

    redis_base = run_base()
    questions = generate_questions()
    vk_session = vk_api.VkApi(token=vk_token)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user = event.user_id
            message = event.text

            question_num = read_question_db(redis_base, user)
            if not question_num:
                question_num = 1

            scores = read_scores_db(redis_base, user)
            if not scores:
                scores = 0

            question, answer = chose_question(questions, question_num)

            if message == 'Вопрос':
                vk.messages.send(
                    user_id=user,
                    random_id=get_random_id(),
                    keyboard=default_keyboard().get_keyboard(),
                    message=question
                )

            elif message == 'Сдаться':

                question_num = read_question_db(redis_base, user)
                question_num = int(question_num) + 1
                write_question_db(redis_base, user, question_num)

                vk.messages.send(
                    user_id=user,
                    random_id=get_random_id(),
                    keyboard=keyboard_without_draw().get_keyboard(),
                    message=f'Правильный ответ {answer} \n'
                            f'Чтобы перейти к следующему вопросу, нажми "Новый вопрос"'
                )

            elif message == 'Мой счет':
                vk.messages.send(
                    user_id=user,
                    random_id=get_random_id(),
                    keyboard=keyboard_without_draw().get_keyboard(),
                    message=f'Твой счет: {scores}'
                )

            else:
                if compare_phrases(message, answer):

                    scores = int(scores) + 1
                    question_num = int(question_num) + 1

                    write_question_db(redis_base, user, question_num)
                    write_scores_db(redis_base, user, question_num)

                    vk.messages.send(
                        user_id=user,
                        random_id=get_random_id(),
                        keyboard=keyboard_without_draw().get_keyboard(),
                        message=f'Ура, правильно! Твой счет: {scores}.\n'
                                f'Для перехода к новому вопросу нажми "Вопрос"'
                    )
                else:
                    vk.messages.send(
                        user_id=user,
                        random_id=get_random_id(),
                        keyboard=default_keyboard().get_keyboard(),
                        message=f'Пока неверно. Можешь продолжать пробовать или сдаться.'
                    )


if __name__ == '__main__':
    env = Env()
    env.read_env()
    vk_token = env.str('VK_TOKEN')
    main(vk_token)

