from datetime import datetime, timedelta
import json
import urllib.parse
import logging
import os.path

from django.shortcuts import render, render_to_response, RequestContext
from django.contrib import messages
from django.conf import settings
from django.core.files import File
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.generic import View, TemplateView
from django.utils.timezone import utc

from plag import const
from plag.forms import UserInfoForm, PasswordChangeForm, UserPreferencesForm, UserCreationForm
from plag.models import Order, ProtectedResource, Invoice, ScanResult, ScanLog, Query
from plag.services import AccountHomepage, AccountPlagiarismScans, ProtectedResourcesOrder, get_user_preferences, \
    get_scan_frequencies_for_order, process_homepage_trial, post_process_index_trial


class IndexView(TemplateView):
    template_name = 'plag/static/index.html'

    def get_context_data(self, **kwargs):
        return {'accepted_file_exts': const.ACCEPTED_FILE_EXTENSIONS}


@login_required
def account(request, template='plag/dynamic/account.html'):
    ctx = {}

    acct_home = AccountHomepage(request.user)
    ctx.update(acct_home.get_text_summary())
    ctx.update(acct_home.get_graph_plag_per_month())
    ctx.update(acct_home.get_chart_content_types())
    ctx.update(acct_home.get_chart_scan_freqs())
    ctx.update(acct_home.get_invoices())

    return render_to_response(template, ctx, context_instance=RequestContext(request))


@login_required
def recent_scans(request, num_days=30, hide_zero='', template='plag/dynamic/recent_scans.html'):
    ctx = {}

    if int(num_days) < 1 or int(num_days) > 30:
        num_days = 30

    ctx.update(
        {'results': AccountPlagiarismScans.get_recent_finds(request.user.id, num_days, True if hide_zero else False)})
    ctx.update({'num_days': num_days})
    ctx.update({'hide_zero': hide_zero})

    return render_to_response(template, ctx, context_instance=RequestContext(request))


@login_required
def invoice(request, pk, template='plag/dynamic/invoice.html'):
    try:
        invoice = Invoice.objects.filter(pk=pk, order__user=request.user)
    except KeyError:
        return redirect('account')

    if invoice:
        return render(request, template, {'invoice': invoice[0]})
    else:
        return redirect('account')


@login_required
def pay_invoice(request, pk):
    try:
        invoice = Invoice.objects.filter(pk=pk, order__user=request.user)
    except KeyError:
        return redirect('account')

    if invoice:
        qs = {
            'cmd': '_xclick',
            'business': 'payments@plagiarismguard.com',
            'item_name': 'Plagiarism Guard',
            'item_number': invoice[0].id,
            'amount': invoice[0].price,
            'currency_code': invoice[0].order.currency,
        }
        url = 'https://www.paypal.com/cgi-bin/webscr?' + urllib.parse.urlencode(qs)
        return redirect(url)
    else:
        return redirect('account')


@login_required
def subscribe_invoice(request, pk):
    try:
        invoice = Invoice.objects.filter(pk=pk, order__user=request.user)
    except KeyError:
        return redirect('account')

    if invoice:
        qs = {
            'cmd': '_xclick-subscriptions',
            'business': 'payments@plagiarismguard.com',
            'item_name': 'Plagiarism Guard',
            'item_number': invoice[0].id,
            'a3': invoice[0].price,
            'p3': '1',
            't3': 'M',
            'currency_code': invoice[0].order.currency,
            'no_note': '1',
            'src': '1',
            'srt': '0',
        }
        url = 'https://www.paypal.com/cgi-bin/webscr?' + urllib.parse.urlencode(qs)
        return redirect(url)
    else:
        return redirect('account')


def ipn(request):
    ProtectedResourcesOrder.handle_paypal_ipn(request)
    return HttpResponse('')


@login_required
def scan_history(request, hide_zero='', template='plag/dynamic/scan_history.html'):
    ctx = {}

    finds = AccountPlagiarismScans.get_historical_finds(request.user.id, True if hide_zero else False)

    user_pref = get_user_preferences(request.user)
    if user_pref and user_pref.results_per_page:
        results_per_page = user_pref.results_per_page
    else:
        results_per_page = const.RESULTS_PER_PAGE

    # https://docs.djangoproject.com/en/1.7/topics/pagination/
    paginator = Paginator(finds, results_per_page)

    page = request.GET.get('page')
    try:
        results = paginator.page(page)
    except PageNotAnInteger:
        results = paginator.page(1)
    except EmptyPage:
        results = paginator.page(paginator.num_pages)

    ctx.update({'results': results})
    ctx.update({'hide_zero': hide_zero})

    return render_to_response(template, ctx, context_instance=RequestContext(request))


@login_required
def download_file(request, prot_res_id):
    prot_res = ProtectedResource.objects.filter(id=prot_res_id, order__user=request.user)

    if prot_res:
        filename = prot_res[0].file.name.split('/')[-1]
        response = HttpResponse(prot_res[0].file, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response


def sitemap_to_urls(request):
    return_data = ProtectedResourcesOrder.get_urls_from_sitemap(request.GET.get('sitemap_url'))
    return HttpResponse(json.dumps(return_data), content_type="application/json")


@login_required
# TODO This excludes ones which haven't been post scanned. But the overall count does not. Also this doesn't look at false positives
def plagiarism_results(request, scan_id=-1):
    scan_results = ScanResult.objects.filter(result_log=scan_id,
                                             result_log__protected_resource__order__user=request.user,
                                             post_scanned=True)

    return_data = []
    for result in scan_results:
        return_data.append({
            'match_url': result.match_url,
            'match_display_url': result.match_display_url,
            'match_title': result.match_title,
            'match_desc': result.match_desc,
            'perc_of_duplication': str(result.perc_of_duplication),
        })

    return HttpResponse(json.dumps(return_data), content_type="application/json")


class ProfileView(View):
    template = 'plag/dynamic/profile.html'

    def get(self, request, *args, **kwargs):
        ctx = {
            'form': UserInfoForm(instance=request.user),
            'pref_form': UserPreferencesForm(instance=get_user_preferences(request.user)),
            'pass_form': PasswordChangeForm(user=request.user),
        }

        return render_to_response(self.template, ctx, context_instance=RequestContext(request))

    def post(self, request, *args, **kwargs):
        f = UserInfoForm(request.POST, instance=request.user)
        pref = UserPreferencesForm(request.POST, instance=get_user_preferences(request.user))
        passwd = None
        valid = f.is_valid() and pref.is_valid()

        if "changing_password" in request.POST:
            passwd = PasswordChangeForm(user=request.user, data=request.POST)

            if passwd.is_valid():
                new_password = passwd.cleaned_data['new_password']
                # Bind the password change to the main form change. If there's an error there, don't change the password
                f.instance.set_password(new_password)
            else:
                valid = False

        if valid:
            pref.save()
            f.save()
            messages.success(request, 'Account information updated')
            return redirect('profile')
        else:
            ctx = {
                'form': f,
                'pref_form': pref,
                'pass_form': passwd if passwd else PasswordChangeForm(user=request.user),
            }
            return render_to_response(self.template, ctx, context_instance=RequestContext(request))


# TODO The 'go back' icon for an existing resource doesn't reset the form
class ProtectedResources(View):
    template = 'plag/dynamic/protected_resource.html'

    def get(self, request, *args, **kwargs):
        ctx = {
            'prot_res': ProtectedResourcesOrder.get_prot_res(request.user),
            'scan_frequencies': ProtectedResource.SCAN_FREQUENCY,
            'accepted_file_exts': const.ACCEPTED_FILE_EXTENSIONS,
            'order': Order.objects.filter(user=request.user, is_active=True)[0],
            'numDaily': 0,
            'numWeekly': 0,
            'numMonthly': 0,
        }

        scan_freqs = get_scan_frequencies_for_order(request.user)
        for freq in scan_freqs:
            if freq['scan_frequency'] == ProtectedResource.DAILY:
                ctx.update({'numDaily': freq['dcount']})
            elif freq['scan_frequency'] == ProtectedResource.WEEKLY:
                ctx.update({'numWeekly': freq['dcount']})
            elif freq['scan_frequency'] == ProtectedResource.MONTHLY:
                ctx.update({'numMonthly': freq['dcount']})

        return render_to_response(self.template, ctx, context_instance=RequestContext(request))

    def post(self, request, *args, **kwargs):
        redirect_loc, param = ProtectedResourcesOrder.handle_amended_order(request)
        if param:
            return redirect(redirect_loc, pk=param)
        else:
            return redirect(redirect_loc)


class OrderView(View):
    template = 'plag/dynamic/order.html'

    def get(self, request, *args, **kwargs):
        ctx = {
            'scan_frequencies': ProtectedResource.SCAN_FREQUENCY,
            'accepted_file_exts': const.ACCEPTED_FILE_EXTENSIONS,
            'user_form': UserCreationForm,
        }

        return render_to_response(self.template, ctx, context_instance=RequestContext(request))

    def post(self, request, *args, **kwargs):
        redirect_loc, param = ProtectedResourcesOrder.handle_new_order(request)
        if param:
            return redirect(redirect_loc, pk=param)
        else:
            return redirect(redirect_loc)


class IndexTrialView(View):
    template = 'plag/static/index_trial.html'

    def get(self, request, *args, **kwargs):
        scan_log_id = request.GET.get('id1')
        scan_result_id = request.GET.get('id2')
        result = post_process_index_trial(request, scan_log_id, scan_result_id)
        perc_dup = result.perc_of_duplication if result else -1

        return HttpResponse(json.dumps({'id': scan_result_id, 'perc_dup': perc_dup, }), content_type="application/json")

    def post(self, request, *args, **kwargs):
        results = process_homepage_trial(request)

        ctx = {
            'scan_log': results[0],
            'scan_results': results[1],
        }

        return render_to_response(self.template, ctx, context_instance=RequestContext(request))


def username_unique(request):
    return_data = False

    username = request.GET.get("username")
    if username:
        user = User.objects.filter(username=username)
        if not user:
            return_data = True

    return HttpResponse(json.dumps(return_data), content_type="application/json")


def data_cleanse(request):
    user = User.objects.get(username='tristanperry')

    for order in Order.objects.all():
        order.delete()

    new_order = Order(user=user, renewal_day=1, price=19.45, currency=Order.USD, is_active=True,
                      time_order_added=datetime.now())
    new_order.save()

    for prot_res in ProtectedResource.objects.all():
        prot_res.delete()

    past_date = datetime.now() - timedelta(days=5)
    url1 = ProtectedResource(order=new_order, url='http://www.diveinto.org/python3/serializing.html',
                             type=ProtectedResource.URL, status=ProtectedResource.A,
                             scan_frequency=ProtectedResource.DAILY, next_scan=past_date)
    url1.save()

    url2 = ProtectedResource(order=new_order, url='http://www.pontypoolpodiatrychiropody.co.uk/',
                             type=ProtectedResource.URL, status=ProtectedResource.A,
                             scan_frequency=ProtectedResource.DAILY, next_scan=past_date)
    url2.save()

    sentiment_analysis = File(open(r'C:\PlagiarismGuard\mediaroottest\testfiles\Sentiment Analysis.pdf', mode='rb'))
    file1 = ProtectedResource(order=new_order, file=sentiment_analysis, type=ProtectedResource.PDF,
                              status=ProtectedResource.A, scan_frequency=ProtectedResource.DAILY,
                              next_scan=past_date, original_filename='Sentiment Analysis.pdf')
    file1.save()

    johnny_sell = File(open(r'C:\PlagiarismGuard\mediaroottest\testfiles\Why Johnny Cant Sell.PDF', mode='rb'))
    file2 = ProtectedResource(order=new_order, file=johnny_sell, type=ProtectedResource.PDF,
                              status=ProtectedResource.A, scan_frequency=ProtectedResource.DAILY,
                              next_scan=past_date, original_filename='Why Johnny Cant Sell.PDF')
    file2.save()

    random_docx = File(open(r'C:\PlagiarismGuard\mediaroottest\testfiles\Random Doc.docx', mode='rb'))
    file3 = ProtectedResource(order=new_order, file=random_docx, type=ProtectedResource.DOCX,
                              status=ProtectedResource.A, scan_frequency=ProtectedResource.DAILY,
                              next_scan=past_date, original_filename='Random Doc.docx')
    file3.save()

    intro_nlp = File(open(r'C:\PlagiarismGuard\mediaroottest\testfiles\Introduction to NLP.pptx', mode='rb'))
    file4 = ProtectedResource(order=new_order, file=intro_nlp, type=ProtectedResource.PPTX,
                              status=ProtectedResource.A, scan_frequency=ProtectedResource.DAILY,
                              next_scan=past_date, original_filename='Introduction to NLP.pptx')
    file4.save()

    cl_links = File(open(r'C:\PlagiarismGuard\mediaroottest\testfiles\ComputerLover links.txt', mode='r'))
    file5 = ProtectedResource(order=new_order, file=cl_links, type=ProtectedResource.TXT,
                              status=ProtectedResource.A, scan_frequency=ProtectedResource.DAILY,
                              next_scan=past_date, original_filename='ComputerLover links.txt')
    file5.save()

    bronafon_pack = File(open(r'C:\PlagiarismGuard\mediaroottest\testfiles\BronAfonApplicationPack.doc', mode='rb'))
    file6 = ProtectedResource(order=new_order, file=bronafon_pack, type=ProtectedResource.DOC,
                              status=ProtectedResource.A, scan_frequency=ProtectedResource.DAILY,
                              next_scan=past_date, original_filename='BronAfonApplicationPack.doc')
    file6.save()

    for invoice in Invoice.objects.all():
        invoice.delete()

    invoice = Invoice(order=new_order, price=94815.12, explanation='This invoice is a rip off')
    invoice.save()

    for hist in ScanResult.objects.all():
        hist.delete()

    for log in ScanLog.objects.all():
        log.delete()

    for query in Query.objects.all():
        query.delete()

    return render(request, 'plag/dynamic/data_cleanse.html')