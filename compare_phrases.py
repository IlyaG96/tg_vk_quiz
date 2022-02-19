from string import punctuation
from fuzzy_match import algorithims


def clear_phrase(phrase):
    phrase = phrase.lower().strip('')

    for symbol in punctuation:
        phrase = phrase.replace(symbol, '')

    return phrase


def compare_phrases(user_answer, quiz_answer):

    user_answer = clear_phrase(user_answer)
    quiz_answer = clear_phrase(quiz_answer)

    sin_compare = algorithims.cosine(user_answer, quiz_answer)
    trigram_compare = algorithims.trigram(user_answer, quiz_answer)
    compare_percentage = ((sin_compare + trigram_compare)/2)*100

    return True if compare_percentage >= 50 else False
