import zipfile
import re

from django.utils.html import strip_tags

from util.textcleanup import split_into_chunks, calculate_unique_score_for_chunk, remove_special_characters
from util.handlequeries import build_query_result


def get_queries(source, num_queries=3):
    scored_chunks = []
    zip_data = zipfile.ZipFile(source).read('word/document.xml')
    try:
        # Word docs seem to always be encoded as UTF-8.
        # TODO Should really scan the encoding attribute, but for now just use this method
        xml = zip_data.decode('UTF-8')
    except UnicodeDecodeError:
        xml = zip_data.decode('ISO-8859-1')

    # Clean up the data - e.g. by replacing 'key' XML like linebreaks into actual linebreaks
    text = xml.replace('<w:br/>', " \r\n");
    text = text.replace('</w:r></w:p></w:tc><w:tc>', " ");
    text = text.replace('</w:r><w:proofErr w:type="gramEnd"/></w:p>', " \r\n");
    text = text.replace('</w:r></w:p>', " \r\n");
    text = re.sub(r'<w:hyperlink.*?<w:t>(.*?)</w:t>.*?</w:hyperlink>', r' \1 ', text)  # extract hyperlink text
    text = re.sub(r'<w:instrText.*?</w:instrText>', '', text)  # remove 'instruction text' fields
    text = re.sub(r'HYPERLINK ".*?"', '', text)
    text = strip_tags(text)

    scored_chunks = []

    for chunk in split_into_chunks(text, filter_poor_quality=True):
        score = calculate_unique_score_for_chunk(chunk)
        scored_chunks.append((remove_special_characters(chunk), score))

    return build_query_result(scored_chunks, num_queries, source=text)