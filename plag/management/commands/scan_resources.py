from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils.timezone import utc

from util.handlequeries import run_request
from util.getqueriespertype import url, txt, pdf, doc, docx, pptx
from plag.models import ProtectedResource, ScanResult, ScanLog, Query

# TODO Implement multi threading and stop phrases
class Command(BaseCommand):
    args = '<number_resources_to_scan>'
    help = 'Gets N protected resources, scans them, and stores the results in the database'

    def handle(self, arg, **options):
        num_to_scan = int(arg)
        now = datetime.utcnow().replace(tzinfo=utc)
        # TODO This will pick out pros res for inactive orders etc - add more filters
        resources = ProtectedResource.objects.filter(next_scan__lt=now).exclude(
            status__in=[ProtectedResource.I, ProtectedResource.P]).order_by('next_scan')[:num_to_scan]

        for resource in resources:
            if resource.type == ProtectedResource.URL:
                queries = url.get_queries(resource.url)
            elif resource.type == ProtectedResource.TXT:
                resource.file.open('r')
                file_data = resource.file.read().decode("utf-8")
                queries = txt.get_queries(file_data)
                resource.file.close()
            elif resource.type == ProtectedResource.PDF:
                resource.file.open('rb')
                queries = pdf.get_queries(resource.file.url)
                resource.file.close()
            elif resource.type == ProtectedResource.DOC:
                resource.file.open('rb')
                queries = doc.get_queries(resource.file.url)
                resource.file.close()
            elif resource.type == ProtectedResource.DOCX:
                resource.file.open('rb')
                queries = docx.get_queries(resource.file)
                resource.file.close()
            elif resource.type == ProtectedResource.PPTX:
                resource.file.open('rb')
                queries = pptx.get_queries(resource.file)
                resource.file.close()
            else:
                continue

            # Save log of result (queries & source)
            if queries['success'] is True:
                log = ScanLog(protected_resource=resource, protected_source=queries['source'])
                log.save()

                query_list = []
                for query in queries['data']:
                    q = Query(query=query)
                    q.save()
                    query_list.append(q)

                log.queries.add(*query_list)
                log.save()

            # Get results from the queries from the resource text and save them to the DB
            if queries['success'] is True and len(queries['data']) > 0:
                results = run_request(queries['data'], [resource.url])

                for result in results:
                    scan_result = ScanResult(result_log=log, match_url=result['url'],
                                             match_display_url=result['displayurl'], match_title=result['title'],
                                             match_desc=result['desc'], post_scanned=False)
                    scan_result.save()

                resource.next_scan = datetime.now() + timedelta(seconds=resource.scan_frequency)
                resource.save()
            else:
                if queries['success'] is True and len(queries['data']) == 0:
                    reason = 'No suitable content found'
                    fail_type = ScanLog.C
                else:
                    log = ScanLog(protected_resource=resource)
                    reason = queries['data']
                    fail_type = ScanLog.H

                log.fail_reason = reason
                log.fail_type = fail_type
                log.save()

                resource.status = ProtectedResource.F
                resource.save()
