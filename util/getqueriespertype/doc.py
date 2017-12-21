import subprocess, os

from django.conf import settings

from util.textcleanup import split_into_chunks, calculate_unique_score_for_chunk, remove_special_characters
from util.handlequeries import build_query_result


def get_queries(filename, num_queries=3):
    scored_chunks = []
    absolute_file_path = os.path.join(settings.MEDIA_ROOT, filename)
    doc_to_text_output = subprocess.check_output([settings.DOC_TO_TEXT, absolute_file_path])
    try:
        text = doc_to_text_output.decode('utf-8')
    except UnicodeDecodeError:
        text = doc_to_text_output.decode('ISO-8859-1')

    scored_chunks = []

    for chunk in split_into_chunks(text, filter_poor_quality=True):
        score = calculate_unique_score_for_chunk(chunk)
        scored_chunks.append((remove_special_characters(chunk), score))

    return build_query_result(scored_chunks, num_queries, source=text)