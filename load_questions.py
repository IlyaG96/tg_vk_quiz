import json
from pprint import pprint
with open(file='questions/6iz36.txt', mode='r', encoding='KOI8-R') as file:
    text = file.read()
questions = {}

text2 = text.split('\n\n')
for item in text2:
    if 'Вопрос' in item:
        question = item
    if 'Ответ' in item:
        answer = item
        questions.update({question: answer})

