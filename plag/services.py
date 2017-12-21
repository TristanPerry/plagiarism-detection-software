import calendar
import decimal
import json
import re
import os
import smtplib
import urllib
import urllib.parse
import uuid
from email.mime.text import MIMEText
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.contrib.auth import login
from django.utils.timezone import utc
from django.db import connection
from django.db.models import Count

from plag.management.commands import post_processing
from plag.models import ProtectedResource, ScanResult, ScanLog, UserPreference, Order, Invoice, Query
from plag.forms import UserCreationForm
from plag import const

from util.getqueriespertype import url, txt, pdf, doc, docx, pptx
from util import handlequeries


def get_scan_frequencies_for_order(user):
    return ProtectedResource.objects.filter(order__user=user, order__is_active=True).exclude(
        status=ProtectedResource.I).values('scan_frequency').annotate(dcount=Count('scan_frequency'))


class AccountHomepage:
    date_now = datetime.utcnow().replace(tzinfo=utc)
    days_in_month = calendar.monthrange(date_now.year, date_now.month)[1]
    date_month_ago = date_now - timedelta(days=days_in_month)

    # Get a date to power a 12 month summary graph (i.e. going from next month last year)
    date_past = date_now + timedelta(
        days=days_in_month)  # put current date to 1st of next month TODO I think this is wrong? If 31st August, wouldn't it skip September??
    date_past = date_past.replace(year=date_past.year - 1, day=1)

    def __init__(self, user):
        self.user = user

    def get_text_summary(self):
        # A basic 'since your last visit, we have carried out N scans and found Y bits of plagiarism' statistic
        # TODO Add 'Of which, X is new plagiarism' - a tricky but useful stat
        stat_plag_summary_scans = ScanLog.objects.filter(protected_resource__order__user=self.user,
                                                         timestamp__gt=self.user.last_login).count()

        stat_type = ''

        if stat_plag_summary_scans:
            fallback_stat = False
            comparison_date = self.user.last_login
            stat_type = 'Login'
        else:
            fallback_stat = True
            comparison_date = self.date_month_ago
            stat_plag_summary_scans = ScanLog.objects.filter(protected_resource__order__user=self.user,
                                                             timestamp__gt=self.date_month_ago).count()
            if stat_plag_summary_scans:
                stat_type = 'Month'

        stat_plag_summary_discovered = ScanResult.objects.filter(result_log__protected_resource__order__user=self.user,
                                                                 timestamp__gt=comparison_date).count()

        return {
            'num_days_since_login': (self.date_now - self.user.last_login).days,
            'stat_plag_summary_scans': stat_plag_summary_scans,
            'stat_plag_summary_discovered': stat_plag_summary_discovered,
            'stat_plag_summary_show': stat_type,
        }

    def get_graph_plag_per_month(self):
        # A graph going from 12 months ago to today, showing (per month) the quantity of plagiarism found
        truncate_date = connection.ops.date_trunc_sql('month', 'plag_scanresult.timestamp')
        graph_plag_summary = ScanResult.objects.extra(select={'month': truncate_date}).values('month').annotate(
            dcount=Count('timestamp')).filter(timestamp__gt=self.date_past,
                                              result_log__protected_resource__order__user=self.user)

        graph_plag_summary_labels = []
        graph_plag_summary_data = []

        # The above DB call will only bring back months with >0 plagiarism. So fill in any other months with 0
        if graph_plag_summary:
            working_date = None
            for i in range(0, 12):
                if working_date is None:
                    working_date = self.date_past
                else:
                    days_to_add = calendar.monthrange(working_date.year, working_date.month)[1]
                    working_date = working_date + timedelta(days=days_to_add)  # go to 1st of next month

                iso_format_date = working_date.strftime("%Y-%m-%d")
                screen_format_date = working_date.strftime("%B %Y")
                graph_plag_summary_labels.append(screen_format_date)

                db_row = [row for row in graph_plag_summary if row['month'] == iso_format_date]

                if db_row:
                    graph_plag_summary_data.append(db_row[0]['dcount'])
                else:
                    graph_plag_summary_data.append(0)

        return {
            'graph_plag_summary_show': True if graph_plag_summary else False,
            'graph_plag_summary_labels': json.dumps(graph_plag_summary_labels),
            'graph_plag_summary_data': json.dumps(graph_plag_summary_data),
        }

    def get_chart_content_types(self):
        # Get a % breakdown of content types (pie chart)
        content_types = ProtectedResource.objects.filter(order__user=self.user).exclude(
            status=ProtectedResource.I).values('type').annotate(dcount=Count('type'))
        show_content_types = True if len(content_types) > 1 else False

        if show_content_types:
            for type in content_types:
                if type['type'] == ProtectedResource.URL:
                    type.update(const.RED)
                elif type['type'] == ProtectedResource.PDF:
                    type.update(const.TURQUOISE)
                elif type['type'] == ProtectedResource.DOC:
                    type.update(const.BROWN)
                elif type['type'] == ProtectedResource.DOCX:
                    type.update(const.YELLOW)
                elif type['type'] == ProtectedResource.PPTX:
                    type.update(const.PURPLE)
                elif type['type'] == ProtectedResource.TXT:
                    type.update(const.BLUE)

        return {
            'graph_content_types_show': show_content_types,
            'graph_content_types': content_types,
        }

    def get_chart_scan_freqs(self):
        # Get a % breakdown of scanning frequencies (pie chart)
        scanning_frequencies = get_scan_frequencies_for_order(self.user)
        show_scan_frequencies = True if len(scanning_frequencies) > 1 else False

        if show_scan_frequencies:
            for scan_freq in scanning_frequencies:
                if scan_freq['scan_frequency'] == ProtectedResource.DAILY:
                    scan_freq.update(const.PURPLE)
                elif scan_freq['scan_frequency'] == ProtectedResource.WEEKLY:
                    scan_freq.update(const.TURQUOISE)
                elif scan_freq['scan_frequency'] == ProtectedResource.MONTHLY:
                    scan_freq.update(const.YELLOW)

                # Change to description form
                scan_freq['scan_frequency'] = [freq[1] for freq in ProtectedResource.SCAN_FREQUENCY if
                                               freq[0] == scan_freq['scan_frequency']][0]

        return {
            'graph_scan_frequencies_show': show_scan_frequencies,
            'graph_scan_frequencies': scanning_frequencies,
        }

    def get_invoices(self):
        unpaid_invoices = Invoice.objects.filter(order__user=self.user, paid__isnull=True).order_by('-id')
        paid_invoices = Invoice.objects.filter(order__user=self.user, paid__isnull=False).order_by('-id')

        return {
            'unpaid_invoices': unpaid_invoices,
            'paid_invoices': paid_invoices,
        }


class AccountPlagiarismScans:
    # TODO Exclude ones which haven't been post scanned
    @staticmethod
    def get_recent_finds(user_id, num_days, hide_zero=False):
        # 'Grouped' at the result log level - i.e. one scan (with N results) is one table row
        date_now = datetime.utcnow().replace(tzinfo=utc)
        date_n_days_ago = date_now - timedelta(days=int(num_days))

        if hide_zero:
            return ScanLog.objects.annotate(num_results=Count('scanresult')).filter(
                protected_resource__order__user=user_id, timestamp__gt=date_n_days_ago,
                num_results__gt=0).select_related('protected_resource').defer('protected_source').order_by('-timestamp')
        else:
            return ScanLog.objects.annotate(num_results=Count('scanresult')).filter(
                protected_resource__order__user=user_id, timestamp__gt=date_n_days_ago).select_related(
                'protected_resource').defer('protected_source').order_by('-timestamp')

    @staticmethod
    def get_historical_finds(user_id, hide_zero=False):
        if hide_zero:
            return ScanLog.objects.annotate(num_results=Count('scanresult')).filter(
                protected_resource__order__user=user_id, num_results__gt=0).select_related(
                'protected_resource').defer('protected_source').order_by('-timestamp')
        else:
            return ScanLog.objects.annotate(num_results=Count('scanresult')).filter(
                protected_resource__order__user=user_id).select_related(
                'protected_resource').defer('protected_source').order_by('-timestamp')


class ProtectedResourcesOrder:
    @staticmethod
    def get_prot_res(user):
        results = []

        prot_res = ProtectedResource.objects.filter(order__user=user, order__is_active=True)

        for res in prot_res:
            scan_log = ScanLog.objects.annotate(num_results=Count('scanresult')).filter(
                protected_resource=res).order_by('-id')
            results.append({
                'prot_res': res,
                'scan_freq': [freq[1] for freq in ProtectedResource.SCAN_FREQUENCY if freq[0] == res.scan_frequency][0],
                'last_scanned': scan_log[0].timestamp if scan_log else '-',
                'last_scanned_num': scan_log[0].num_results if scan_log else '-',
            })

        return results

    @staticmethod
    def get_urls_from_sitemap(url):
        if url is None:
            return []

        try:
            url_result = requests.get(url, timeout=5, headers={
                'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36',
                'Connection': 'close',
            })

            if url_result.status_code != 200:
                return []
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            return []

        urls = re.findall(r'<loc>(http://.+)</loc>', url_result.text)
        return urls

    @staticmethod
    def handle_amended_order(request):
        """
        Existing prot res can be seen via:
            * existing_prot_res_id
            * existing_pros_res_scan_freq_[num]
            * existing_prot_res_url_[num]
            * existing_prot_res_file_[num]
        Where [num] matches that row's existing_prot_res_id
        An existing prot res might have changed - but within the same type (URL -> URL, file -> file).

        New prot res can be seen via:
            * new_prot_res_url_[num]
            * new_prot_res_file_[num]
            * new_pros_res_scan_freq_[num]

        Where [num] is between 0 and numMaxNewProtRes.

        It's possible for someone to 'add' a new prot res, but leave both the URL and file blank.
        In this case, assign the type to be a URL and proceed. (We show on screen validation, and error handling would
        be a PITA, so this is the easiest method - albeit it might annoy a fraction of users).

        Where a file with an 'unknown' extension is uploaded, set it to text file type.

        :return: A string containing a URL/path of where to take the user after processing is complete.
        """
        # Firstly get a new order entity, so the new prot res can refer to it. We can always update the price later
        order = Order.objects.filter(user=request.user, is_active=True)[0]
        order.is_active = False
        old_price = order.price
        order.save()

        order.pk = None
        order.is_active = True
        order.time_order_added = datetime.utcnow().replace(tzinfo=utc)
        order.save()

        # Will bulk save later, after knowing whether the status should be A (active) or P (awaiting payment)
        new_protected_resources = []
        num_daily = 0
        num_weekly = 0
        num_monthly = 0

        print('-----------')
        print('Existing')
        print('-----------')
        params_existing_id = request.POST.getlist('existing_prot_res_id')

        for param_id in params_existing_id:
            # TODO Creating a new prot res loses all scan results... maybe change the prot res in the scan log (to the new one?)
            old_prot_res = ProtectedResource.objects.filter(pk=param_id)[0]
            param_existing_freq = request.POST.get('existing_pros_res_scan_freq_' + param_id)
            param_existing_url = request.POST.get('existing_prot_res_url_' + param_id)
            param_existing_file = request.FILES.get('existing_prot_res_file_' + param_id)

            new_prot_res = ProtectedResource()
            new_prot_res.order = order
            new_prot_res.next_scan = old_prot_res.next_scan
            new_prot_res.type = old_prot_res.type

            scan_freq_map = [freq[0] for freq in ProtectedResource.SCAN_FREQUENCY if freq[1] == param_existing_freq]
            if scan_freq_map:
                new_prot_res.scan_frequency = scan_freq_map[0]
            else:
                new_prot_res.scan_frequency = old_prot_res.scan_frequency

            if new_prot_res.scan_frequency == ProtectedResource.DAILY:
                num_daily += 1
            elif new_prot_res.scan_frequency == ProtectedResource.WEEKLY:
                num_weekly += 1
            elif new_prot_res.scan_frequency == ProtectedResource.MONTHLY:
                num_monthly += 1

            if old_prot_res.type == ProtectedResource.URL:
                if param_existing_url != old_prot_res.url:
                    new_prot_res.url = param_existing_url
                else:
                    new_prot_res.url = old_prot_res.url
            else:
                if param_existing_file is not None:
                    new_prot_res.file = param_existing_file
                    new_prot_res.original_filename = param_existing_file.name
                else:
                    new_prot_res.file = old_prot_res.file
                    new_prot_res.original_filename = old_prot_res.original_filename

            new_protected_resources.append(new_prot_res)

        extra_prot_res, price, explanation = ProtectedResourcesOrder.generate_prot_res_from_new(request, order,
                                                                                                num_daily, num_weekly,
                                                                                                num_monthly)
        new_protected_resources = new_protected_resources + extra_prot_res

        TWO_PLACES = decimal.Decimal(10) ** -2
        order.price = decimal.Decimal(price).quantize(TWO_PLACES)
        old_price = old_price.quantize(TWO_PLACES)

        if order.price > old_price:
            price_inc = order.price - old_price
            inc_explanation = "<li>${0:.2f} due today, then ${1:.2f} due thereafter on your usual payment date.</li>".format(
                price_inc, order.price)

            invoice = Invoice()
            invoice.order = order
            invoice.price = price_inc
            invoice.explanation = explanation + inc_explanation
            invoice.is_adjustment = True

            order.save()
            invoice.save()
            for prot_res in new_protected_resources:
                prot_res.status = ProtectedResource.P
                prot_res.save()

            return 'invoice', invoice.id
        else:
            order.save()

            for prot_res in new_protected_resources:
                prot_res.status = ProtectedResource.P
                prot_res.save()

            return 'protected_resources', None

    @staticmethod
    def generate_prot_res_from_new(request, order, num_daily=0, num_weekly=0, num_monthly=0):
        """
        Creates a list of unsaved protected resource entities, along with a price and price explanation
        :param request:
        :param num_daily:
        :param num_weekly:
        :param num_monthly:
        :return: A tuple of protected resources [0], price [1] and explanation [2]
        """
        new_protected_resources = []

        try:
            max_iters = int(request.POST.get('numMaxNewProtRes', 0))
        except TypeError:
            max_iters = 0

        # TODO A new prot res can be deleted, hence all params will be None - handle this case (don't add it)
        for param_id in range(0, max_iters):
            param_url = request.POST.get('new_prot_res_url_' + str(param_id))
            param_file = request.FILES.get('new_prot_res_file_' + str(param_id))
            param_scan_freq = request.POST.get('new_pros_res_scan_freq_' + str(param_id))

            new_prot_res = ProtectedResource()
            new_prot_res.order = order
            new_prot_res.next_scan = datetime.utcnow().replace(tzinfo=utc)

            scan_freq_map = [freq[0] for freq in ProtectedResource.SCAN_FREQUENCY if freq[1] == param_scan_freq]
            if scan_freq_map:
                new_prot_res.scan_frequency = scan_freq_map[0]
            else:
                new_prot_res.scan_frequency = ProtectedResource.DAILY

            if new_prot_res.scan_frequency == ProtectedResource.DAILY:
                num_daily += 1
            elif new_prot_res.scan_frequency == ProtectedResource.WEEKLY:
                num_weekly += 1
            elif new_prot_res.scan_frequency == ProtectedResource.MONTHLY:
                num_monthly += 1

            if param_url:
                new_prot_res.type = ProtectedResource.URL
                new_prot_res.url = param_url
            elif param_file is not None:
                extension = os.path.splitext(param_file.name)[1][1:]
                extension = extension.upper() if extension is not None else ''

                if extension == ProtectedResource.PDF:
                    new_prot_res.type = ProtectedResource.PDF
                elif extension == ProtectedResource.DOC:
                    new_prot_res.type = ProtectedResource.DOC
                elif extension == ProtectedResource.DOCX:
                    new_prot_res.type = ProtectedResource.DOCX
                elif extension == ProtectedResource.PPTX:
                    new_prot_res.type = ProtectedResource.PPTX
                elif extension == ProtectedResource.TXT:
                    new_prot_res.type = ProtectedResource.TXT
                else:
                    new_prot_res.type = ProtectedResource.TXT

                new_prot_res.file = param_file
                new_prot_res.original_filename = param_file.name
            else:
                new_prot_res.type = ProtectedResource.URL
                new_prot_res.url = ''

            new_protected_resources.append(new_prot_res)

        price, explanation = ProtectedResourcesOrder.calculate_price(num_daily, num_weekly, num_monthly)

        return new_protected_resources, price, explanation


    @staticmethod
    def handle_new_order(request):
        # Returns a URL name and (optional) parameter for the redirect
        user_form = UserCreationForm(request.POST)

        if not user_form.errors:
            user = user_form.save()

            order = Order()
            order.renewal_day = datetime.utcnow().replace(tzinfo=utc).strftime("%d")
            order.currency = Order.USD
            order.is_active = True
            order.user = user
            order.price = 0.00
            order.save()

            prot_res, price, explanation = ProtectedResourcesOrder.generate_prot_res_from_new(request, order)
            order.price = price
            order.save()

            invoice = Invoice()
            invoice.order = order
            invoice.price = price
            invoice.explanation = explanation
            invoice.is_adjustment = False
            invoice.save()

            for res in prot_res:
                res.status = ProtectedResource.P
                res.save()

            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            return 'invoice', invoice.id
        else:
            # TODO Errors should be rare, but obviously the return order data should be kept when going back to the order form - ATM all data is lost!!
            return 'order', None


    @staticmethod
    def calculate_price(num_daily, num_weekly, num_monthly):
        """
        Calculates a price based on scan frequency, returning the price and explanation in a tuple
        :param num_daily:
        :param num_weekly:
        :param num_monthly:
        :return: A tuple of price [0] and explanation [1]
        """
        daily_mod = 23
        weekly_mod = 4
        per_charge = 0.04

        price_daily = num_daily * daily_mod * per_charge
        price_weekly = num_weekly * weekly_mod * per_charge
        price_monthly = num_monthly * per_charge
        price = price_daily + price_weekly + price_monthly
        explanation = ''

        if price_daily > 0:
            explanation += "<li>{0} resources with daily protection = ${1:.2f}</li>".format(num_daily, price_daily)

        if price_weekly > 0:
            explanation += "<li>{0} resources with weekly protection = ${1:.2f}</li>".format(num_weekly, price_weekly)

        if price_monthly > 0:
            explanation += "<li>{0} resources with monthly protection = ${1:.2f}</li>".format(num_monthly,
                                                                                              price_monthly)

        if price < 3.5:
            price = 3.5
            explanation += "<li>Minimum order is $3.50 per month.</li>"

        return price, explanation


    @staticmethod
    def handle_paypal_ipn(request):
        if request.method == 'POST':
            data = dict(request.POST.items())

            verify_url = 'https://www.paypal.com/cgi-bin/webscr?cmd=_notify-validate'
            with urllib.request.urlopen(verify_url, urllib.parse.urlencode(data).encode('UTF-8')) as url:
                verify_data = url.read()

            if verify_data == 'VERIFIED':
                ProtectedResourcesOrder.handle_successful_paypal_ipn(data)
            else:
                ProtectedResourcesOrder.handle_invalid_paypal_ipn(data)


    @staticmethod
    def handle_successful_paypal_ipn(data):
        invoice_id = data['item_number']
        payment_status = data['payment_status']
        txn_id = data['txn_id']
        receiver_email = data['receiver_email']
        business_email = data['business'] if data.get('business') else data['receiver_email']
        payer_email = data['payer_email']

        email = "A valid PayPal IPN was received. The invoice ID is {0}, payment status is {1}, TXN ID is {2}, payer email is {3} and receiver email is {4}".format(
            invoice_id, payment_status, txn_id, payer_email, receiver_email)
        send_mail(email, 'PayPal IPN')

        if payment_status == 'Completed' and business_email == 'payments@plagiarismguard.com':
            invoice = Invoice.objects.filter(pk=invoice_id)[0]
            invoice.paypal_tid = txn_id
            invoice.paid = datetime.utcnow().replace(tzinfo=utc)
            invoice.save()

            # Update any prot res related to this invoice/order which are awaiting payment
            prot_res = ProtectedResource.objects.filter(status=ProtectedResource.P, order=invoice.order)
            if prot_res:
                for res in prot_res:
                    res.status = ProtectedResource.A
                    res.save()

            send_mail('The PayPal IPN related to a Plagiarism Guard invoice', 'Plagiarism Guard PayPal payment')


    @staticmethod
    def handle_invalid_paypal_ipn(data):
        payer_email = data['payer_email'] if data.get('payer_email') else 'unknown'
        item_num = data['item_number'] if data.get('item_number') else 'unknown'

        send_mail("An invalid PayPal IPN was received. The payer's email is {0} and the item number is {1}".format(
            payer_email, item_num), 'PayPal IPN')


def process_homepage_trial(request):
    """
    Processes the HTTP request and scans the URL or file, returning the ID of the homepage trial.

    :param request: The HTTP request
    :return: Tuple of [0] the scan log and [1] a list of results (if applicable)
    """
    scan_results = []
    param_url = request.POST.get('url')
    param_file = request.FILES.get('plagFile')

    if param_url:
        queries = url.get_queries(param_url)
    elif param_file:
        extension = os.path.splitext(param_file.name)[1][1:]
        extension = extension.upper() if extension is not None else ''

        if extension in [ProtectedResource.PDF, ProtectedResource.DOC,]:
            filename = get_unique_filename(extension)
            file_path = os.path.join(settings.MEDIA_ROOT, filename)
            with open(file_path, 'wb') as dest:
                dest.write(param_file.read())

            if extension == ProtectedResource.PDF:
                queries = pdf.get_queries(filename)
            elif extension == ProtectedResource.DOC:
                queries = doc.get_queries(filename)

            os.remove(file_path)
        elif extension == ProtectedResource.DOCX:
            queries = docx.get_queries(param_file)
        elif extension == ProtectedResource.PPTX:
           queries = pptx.get_queries(param_file)
        else:
            queries = txt.get_queries(param_file.read().decode("utf-8"))

    # TODO Too similar to scan_resources code
    if queries['success']:
        log = ScanLog(protected_source=queries['source'], user_ip=get_client_ip(request))
        log.save()

        query_list = []
        for query in queries['data']:
            q = Query(query=query)
            q.save()
            query_list.append(q)

        log.queries.add(*query_list)
        log.save()

    if queries['success'] and len(queries['data']) > 0:
        results = handlequeries.run_request(queries['data'], [param_url, ])

        for result in results:
            scan_result = ScanResult(result_log=log, match_url=result['url'],
                                     match_display_url=result['displayurl'], match_title=result['title'],
                                     match_desc=result['desc'], post_scanned=False)
            scan_result.save()
            scan_results.append(scan_result)
    else:
        if queries['success'] and len(queries['data']) == 0:
            reason = 'No suitable content found'
            fail_type = ScanLog.C
        else:
            log = ScanLog(user_ip=get_client_ip(request))
            reason = queries['data']
            fail_type = ScanLog.H

        log.fail_reason = reason
        log.fail_type = fail_type
        log.save()

    return log, scan_results


def post_process_index_trial(request, scan_log_id, scan_result_id):
    user_ip = get_client_ip(request)
    result = ScanResult.objects.filter(pk=scan_result_id, result_log__pk=scan_log_id, result_log__user_ip=user_ip)

    if result:
        return post_processing.post_process_result(result[0])
    else:
        return None


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_unique_filename(extension):
    while True:
        filename = "%s.%s" % (uuid.uuid4(), extension)
        try_path = os.path.join(settings.MEDIA_ROOT, filename)

        if os.path.isfile(try_path):
            continue
        else:
            return filename



def send_mail(body, subject, mail_from='payments@plagiarismguard.com', mail_to='tristan@tristanperry.com'):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = mail_from
    msg['To'] = mail_to

    s = smtplib.SMTP('localhost')
    s.send_message(msg)
    s.quit()


def get_user_preferences(user):
    user_prefs = UserPreference.objects.filter(user=user)

    if not user_prefs:
        user_prefs = UserPreference()
        user_prefs.user = user
        return user_prefs
    else:
        return user_prefs[0]

