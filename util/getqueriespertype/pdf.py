import re, subprocess, os

from django.conf import settings

from util.textcleanup import calculate_unique_score_for_chunk, split_into_chunks, remove_special_characters
from util.handlequeries import build_query_result


def get_queries(filename, num_queries=3):
    '''
    :param filename: The filename for the PDF
    :param num_queries: the number of items in the list to return
    :return: a list of tuples containing the chunk (query) and its score
    '''
    scored_chunks = []
    absolute_file_path = os.path.join(settings.MEDIA_ROOT, filename)
    pdf_to_text_output = subprocess.check_output([settings.PDF_TO_TEXT, "-layout", absolute_file_path, "-"])
    try:
        text = pdf_to_text_output.decode('utf-8')
    except UnicodeDecodeError:
        text = pdf_to_text_output.decode('ISO-8859-1')

    for chunk in split_into_chunks(remove_special_characters(text)):
        ''' Since PDF extraction can be messy and lead to bad results, we use a non standard scoring system (for now):
                +1 if there's 8+ words of length >= 3 characters
                +1 if 75% or more of the non-whitespace characters are alphabetic
            This is to eliminate any clearly crap results '''
        num_words_len3 = 0
        chunk_words = chunk.split()
        for word in chunk_words:
            if len(word) >= 3:
                num_words_len3 += 1

        score = (1 if num_words_len3 >= 8 else 0)

        word_no_whitespace = chunk.replace(' ', '')
        word_only_alpha = re.sub(r'[^a-zA-Z]+', '', word_no_whitespace)
        if len(word_only_alpha) / len(word_no_whitespace) > 0.75:
            score += 1

        scored_chunks.append((chunk, score))

    # Okay, if there's > num_queries chunks with a score of 2, now we'll use uniqueness scoring
    full_score_chunks = [chunk for chunk in scored_chunks if chunk[1] == 2]

    if len(full_score_chunks) > num_queries:
        scored_chunks = []

        for scored_chunk in full_score_chunks:
            unique_score = calculate_unique_score_for_chunk(scored_chunk[0])
            scored_chunks.append((scored_chunk[0], scored_chunk[1]+unique_score))

    return build_query_result(scored_chunks, num_queries, source=text)