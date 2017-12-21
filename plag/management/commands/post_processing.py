import urllib.request
from urllib.error import HTTPError, URLError
from socket import timeout
import threading

from django.core.management.base import BaseCommand

from plag.models import ScanResult, ScanLog
from util.textcleanup import html_to_basic_text, remove_special_characters, generate_ngrams


# TODO Look at ways of killing a thread if it's going on for too long (10 seconds per URL per thread??)
class Command(BaseCommand):
    args = '<number_resources_to_scan number_of_threads>'
    help = 'Gets N scan result histories, and sees whether they are real matches or not - if the former, calculate a % of duplication (via Y threads)'
    scan_results = None
    current_result_idx = 0
    lock = threading.Lock()

    def process_result(self, thread_id):
        print('Thread #' + str(thread_id) + ' starting')

        while self.current_result_idx < len(self.scan_results):
            with self.lock:
                result = self.scan_results[self.current_result_idx]
                self.current_result_idx += 1

            post_process_result(result)

        print('Thread #' + str(thread_id) + ' ending')

    def handle(self, *args, **options):
        num_to_scan = int(args[0])
        num_threads = int(args[1])

        self.scan_results = list(ScanResult.objects.filter(post_scanned=False, post_fail_type__isnull=True).order_by(
            'timestamp')[:num_to_scan])

        for i in range(num_threads):
            t = threading.Thread(target=self.process_result, args=(i,))
            t.start()


def post_process_result(result):
    # If the result is a PDF, Word doc or Powerpoint presentation, skip over it for now (TODO)
    if result.match_url.lower().endswith(('doc','docx','pdf')):
        result.perc_of_duplication = -1
        result.post_scanned = True
        result.save()
        return result

    # Firstly get the HTML for this API result (URL)
    try:
        url_result = urllib.request.urlopen(urllib.request.Request(result.match_url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36'}),
                                            timeout=5).read()
    except (HTTPError, URLError) as e:
        result.perc_of_duplication = -1
        result.post_fail_reason = str(e)
        result.post_fail_type = ScanLog.H
        result.post_scanned = True
        result.save()
        return result
    except timeout as t:
        result.perc_of_duplication = -1
        result.post_fail_reason = 'URL timed out'
        result.post_fail_type = ScanLog.H
        result.post_scanned = True
        result.save()
        return result
    else:
        try:
            url_text = url_result.decode('utf-8')
        except UnicodeDecodeError:
            url_text = url_result.decode('ISO-8859-1')

        result_text = html_to_basic_text(url_text)
        queries_in_result = [query.query for query in result.result_log.queries.all() if
                             remove_special_characters(query.query) in result_text]

        # If no queries exist in the result, this must be a false positive - i.e. Bing has returned rubbish results
        if len(queries_in_result) == 0:
            result.perc_of_duplication = -1
            result.post_fail_reason = 'False positive'
            result.post_fail_type = ScanLog.C
        else:
            # Else the results seem okay, so work out a % duplication based on trigrams (NumMatchedTGs / NumProtectedTGs * 100)
            source_text = html_to_basic_text(result.result_log.protected_source)
            source_trigrams = generate_ngrams(source_text.lower())
            result_trigrams = generate_ngrams(result_text.lower())

            num_trigram_intersection = len(
                [source for source in source_trigrams if source.lower() in result_trigrams])
            result.perc_of_duplication = (num_trigram_intersection / len(source_trigrams)) * 100

        result.post_scanned = True
        result.save()
        return result