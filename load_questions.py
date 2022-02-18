from pprint import pprint
with open(file='questions/1vs1201.txt', mode='r', encoding='KOI8-R') as file:
    raw_text = file.read()

questions = {}
question_number = 1

quiz_text = raw_text.split('\n\n')
for sentence in quiz_text:
    if 'Вопрос' in sentence:
        question = sentence
    if 'Ответ' in sentence:
        answer = sentence

        questions.update({question_number: {question: answer}})
        question_number += 1
