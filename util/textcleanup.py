from math import ceil
import re, os

from bs4 import BeautifulSoup

# TODO Change this (et al) into generators? (yield instead of .append??)
def split_into_chunks(text, num_words=12, ignore_chunks_below_num_words=5, filter_poor_quality=False):
    chunks = []
    # TODO This currently ignores line breaks.
    # Should probably stop each possible sentence/chunk at a new line/paragraph ending?
    words = text.split()
    iterate_times = ceil(len(words) / num_words)

    for x in range(0, iterate_times):
        start_idx = x * num_words
        sub_words = words[start_idx:start_idx + num_words]

        add_chunk = True
        chunk = ' '.join(sub_words)

        # Optionally filter 'poor quality' sentences (where there's less than 50% normal, ASCII printable chars)
        if filter_poor_quality and len(remove_special_characters(chunk))/len(chunk) < 0.5:
            add_chunk = False
        elif len(sub_words) < ignore_chunks_below_num_words:
            add_chunk = False

        if add_chunk:
            chunks.append(chunk)

    return chunks


def stop_words():
    return ["a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't", "as",
            "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't",
            "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
            "each", "few", "for", "from", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd",
            "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
            "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it'd", "it'll", "it's", "its",
            "itself", "let's", "me", "more", "most", "must", "mustn't", "my", "myself", "no", "nor", "not", "of", "off",
            "on", "once", "only", "or", "other", "ought", "our", "ours", "out", "over", "own", "same", "she", "she'd",
            "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", "that", "that'll", "that's", "the",
            "their", "theirs", "them", "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
            "they've", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we",
            "we'd", "we'll", "we're", "we've", "went", "were", "weren't", "what", "what's", "when", "when's", "where",
            "where's", "which", "while", "who", "who's", "whom", "why", "with", "won't", "would", "wouldn't", "you",
            "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", ]


def stop_phrases():
    return ["share this article", "all rights reserved", "contact us", "privacy policy", ]


def calculate_unique_score_for_chunk(chunk, stop_words=stop_words(), stop_phrases=stop_phrases()):
    """ Calculate the uniqueness (and add to parent score) of the given 'chunk'.
        This is calculated as (numWords - numStopWords) / numWords - i.e. higher is better.
            # Score +1 if the uniqueness is >= 35% and < 50%
            # Score +2 if the uniqueness is >= 50% and < 70%
            # Score +3 if the uniqueness is >= 70% and < 90%
            # Score +4 if the uniqueness is >= 90%
        The only caveat is that if a stop phrase is encountered, the score is set to -9 before uniqueness is calculated """
    for stop in stop_phrases:
        if stop in chunk:
            return -9

    words = chunk.split()
    num_stopword_intersection = len([word for word in words if word.lower() in stop_words])
    num_words = len(words)

    unique_perc = (num_words - num_stopword_intersection) / num_words

    if 0.35 <= unique_perc < 0.5:
        return 1
    elif 0.5 <= unique_perc < 0.7:
        return 2
    elif 0.7 <= unique_perc < 0.9:
        return 3
    elif unique_perc >= 0.9:
        return 4
    else:
        return 0


def choose_bs_parser(html):
    """ If the HTMl5 doctype or tags are present, use the HTML5 parser. Else, use the standard Python parser."""
    if re.match(r"<(section|nav|article|aside|header|footer|main).*?>", html) or re.match(r"<!DOCTYPE html>", html,
                                                                                          re.IGNORECASE):
        return "html5lib"
    else:
        return "html.parser"


def remove_special_characters(text):
    return re.sub(r'[^a-zA-Z0-9\'-]+', ' ', text)


def html_to_basic_text(html):
    try:
        soup = BeautifulSoup(html, choose_bs_parser(html))
        basic_text = remove_special_characters(soup.get_text())
        return ' '.join(basic_text.split())  # replace multiple whitespace with a single space
    except Exception:
        return ''


def generate_ngrams(text, n=3):
    words = text.split(' ')
    ngrams = []
    for w in range(len(words) - n + 1):
        ngram = ' '.join(words[w:w + n])
        ngrams.append(ngram)

    return ngrams


def amend_filepath_slashes(path):
    alt_sep = ("\\" if os.sep == "/" else "/")
    return path.replace(os.sep, alt_sep).replace(alt_sep, os.sep)