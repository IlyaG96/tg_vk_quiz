from string import punctuation
from fuzzy_match import algorithims


def clear_phrase(phrase):

    phrase = phrase.lower().strip('')
    cleared_phrase = phrase.translate(str.maketrans('', '', punctuation))

    return cleared_phrase


def compare_phrases(user_answer, quiz_answer):

    user_answer = clear_phrase(user_answer)
    quiz_answer = clear_phrase(quiz_answer)

    sin_compare = algorithims.cosine(user_answer, quiz_answer)
    trigram = algorithims.trigram(user_answer, quiz_answer)

    return True if (sin_compare >= 0.5 or trigram >= 0.5) else False
