from os import listdir
from environs import Env
from pathlib import Path


def generate_questions():

    env = Env()
    env.read_env()
    questions_path = env.str('PATH_TO_QUESTIONS', 'questions')
    questions = {}
    question_start_number = 1
    question_files = listdir(path=questions_path)

    for question_file in question_files:
        file_path = Path(questions_path, question_file)
        with open(file=file_path, mode='r', encoding='KOI8-R') as file:
            raw_text = file.read()

        quiz_text = raw_text.split('\n\n')

        for sentence in quiz_text:
            if 'Вопрос' in sentence:
                question = sentence
            if 'Ответ:' in sentence:
                sentence = sentence.split('Ответ:')
                # we use index 1 because answer always stands after 'Ответ:'
                answer = sentence[1].strip('\n')

                questions.update({question_start_number: {question: answer}})
                question_start_number += 1

    return questions


def chose_question(questions, question_num):

    quiz = questions.get(int(question_num))

    return tuple(quiz.items())
