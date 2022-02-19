from os import listdir


def generate_questions():

    questions = {}
    question_start_number = 1
    question_files = listdir(path='questions')

    for question_file in question_files:

        with open(file=f'questions/{question_file}', mode='r', encoding='KOI8-R') as file:
            raw_text = file.read()

        quiz_text = raw_text.split('\n\n')

        for sentence in quiz_text:
            if 'Вопрос' in sentence:
                question = sentence
            if 'Ответ' in sentence:
                sentence = sentence.split('Ответ')
                answer = sentence[1]

                questions.update({question_start_number: {question: answer}})
                question_start_number += 1

    return questions


def chose_question(questions, question_num):

    quiz = questions.get(int(question_num))

    for quest, ans in quiz.items():
        return quest, ans

