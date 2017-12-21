import zipfile, re, natsort

from django.utils.html import strip_tags

from util.textcleanup import split_into_chunks, calculate_unique_score_for_chunk, remove_special_characters
from util.handlequeries import build_query_result


def get_queries(source, num_queries=3):
    scored_chunks = []
    zip_file = zipfile.ZipFile(source)
    zip_files = zip_file.namelist()
    pattern = r'ppt/slides/slide\d+.xml' # each slide has the format ppt/slides/slide[int].xml
    all_slides = [slide for slide in zip_files if re.search(pattern, slide)]
    all_slides = natsort.natsorted(all_slides, key=lambda y: y.lower())

    scored_chunks = []
    source_text = ''
    for slide in all_slides:
        slide_data = zip_file.read(slide)

        try:
            # Powerpoint presentations seem to always be encoded as UTF-8.
            # Should really scan the encoding attribute, but for now just use this method
            xml = slide_data.decode('UTF-8')
        except UnicodeDecodeError:
            xml = slide_data.decode('ISO-8859-1')

        text = xml.replace('</a:t></a:r>', ' ')
        text = re.sub(r'<p:attrNameLst>.*?</p:attrNameLst>', '', text)
        text = re.sub(r'<a:fld id=".*?" type="slidenum">.*?</a:fld>', '', text)
        text = strip_tags(text)
        source_text += text

        for chunk in split_into_chunks(text, filter_poor_quality=True):
            score = calculate_unique_score_for_chunk(chunk)
            scored_chunks.append((remove_special_characters(chunk), score))

    return build_query_result(scored_chunks, num_queries, source=source_text)