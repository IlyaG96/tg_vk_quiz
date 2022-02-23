from load_questions import generate_questions, chose_question
from compare_phrases import compare_phrases
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from environs import Env
import vk_api
import redis


def build_default_keyboard():

    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Вопрос', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.PRIMARY)

    return keyboard


def build_keyboard_without_draw():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Вопрос', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.PRIMARY)

    return keyboard


def main():

    env = Env()
    env.read_env()
    vk_token = env.str('VK_TOKEN')
    redis_host = env.str('REDIS_HOST')
    redis_port = env.str('REDIS_PORT')
    redis_password = env.str('REDIS_PASSWORD')
    questions = generate_questions()

    redis_base = redis.Redis(host=redis_host,
                             port=redis_port,
                             password=redis_password,
                             decode_responses=True)

    vk_session = vk_api.VkApi(token=vk_token)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user = event.user_id
            message = event.text

            question_num = redis_base.hget(user, 'question_num')
            if not question_num:
                question_num = 1

            scores = redis_base.hget(user, 'scores')
            if not scores:
                scores = 0

            question, answer = chose_question(questions, question_num)

            if message == 'Вопрос':
                vk.messages.send(
                    user_id=user,
                    random_id=get_random_id(),
                    keyboard=build_default_keyboard().get_keyboard(),
                    message=question
                )

            elif message == 'Сдаться':

                question_num = redis_base.hget(user, 'question_num')
                question_num = int(question_num) + 1
                redis_base.hset(user, 'question_num', question_num)

                vk.messages.send(
                    user_id=user,
                    random_id=get_random_id(),
                    keyboard=build_keyboard_without_draw().get_keyboard(),
                    message=f'Правильный ответ {answer} \n'
                            f'Чтобы перейти к следующему вопросу, нажми "Вопрос"'
                )

            elif message == 'Мой счет':
                vk.messages.send(
                    user_id=user,
                    random_id=get_random_id(),
                    keyboard=build_keyboard_without_draw().get_keyboard(),
                    message=f'Твой счет: {scores}'
                )

            else:
                if compare_phrases(message, answer):

                    scores = int(scores) + 1
                    question_num = int(question_num) + 1

                    redis_base.hset(user, 'question_num', question_num)
                    redis_base.hset(user, 'scores', scores)

                    vk.messages.send(
                        user_id=user,
                        random_id=get_random_id(),
                        keyboard=build_keyboard_without_draw().get_keyboard(),
                        message=f'Ура, правильно! Твой счет: {scores}.\n'
                                f'Для перехода к новому вопросу нажми "Вопрос"'
                    )
                else:
                    vk.messages.send(
                        user_id=user,
                        random_id=get_random_id(),
                        keyboard=build_default_keyboard().get_keyboard(),
                        message=f'Пока неверно. Можешь продолжать пробовать или сдаться.'
                    )
