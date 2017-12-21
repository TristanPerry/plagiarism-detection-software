import os

from datetime import datetime, timedelta

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

''' Not moved over (yet):
indextrial - will need
'''


class Order(models.Model):
    GBP = 'GBP'
    EUR = 'EUR'
    USD = 'USD'
    CURRENCIES = (
        (GBP, 'GBP'),
        (EUR, 'EUR'),
        (USD, 'USD'),
    )

    # A user can have multiple orders, if they've amended their order (since we close the old one)
    user = models.ForeignKey(User)
    renewal_day = models.PositiveSmallIntegerField(default=1)
    price = models.DecimalField(max_digits=9, decimal_places=2)  # 9, 2 = N,NNN,NNN.DD
    currency = models.CharField(max_length=3,
                                choices=CURRENCIES,
                                default=USD)
    is_active = models.BooleanField(default=True)
    time_order_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id) + ': ' + str(self.price) + ' ' + self.currency


class ProtectedResource(models.Model):
    # Handling choices below due to http://www.b-list.org/weblog/2007/nov/02/handle-choices-right-way/
    URL = 'URL'
    PDF = 'PDF'
    DOC = 'DOC'
    DOCX = 'DOCX'
    PPTX = 'PPTX'
    TXT = 'TXT'
    RESOURCE_TYPES = (
        (URL, 'Website address'),
        (PDF, 'PDF file'),
        (DOC, 'Word document, old format'),
        (DOCX, 'Word document, new format'),
        (PPTX, 'Powerpoint presentation'),
        (TXT, 'Standard text file'),
    )

    A = 'A'
    N = 'N'
    S = 'S'
    F = 'F'
    P = 'P'
    O = 'O'
    I = 'I'
    STATUS_TYPES = (
        (A, 'Active'),
        (N, 'Newly placed order'),
        (S, 'Being scanned'),
        (F, 'Last scan failed'),
        (P, 'Awaiting payment'),
        (I, 'Inactive'),
    )

    DAILY = 86400
    WEEKLY = 604800
    MONTHLY = 2592000
    SCAN_FREQUENCY = (
        (DAILY, 'Daily'),
        (WEEKLY, 'Weekly'),
        (MONTHLY, 'Monthly'),
    )

    order = models.ForeignKey(Order)
    url = models.CharField(max_length=2048, blank=True)
    file = models.FileField(upload_to='userfiles/%Y/%m/%d', blank=True)
    type = models.CharField(max_length=4, choices=RESOURCE_TYPES, default=URL)
    status = models.CharField(max_length=1, choices=STATUS_TYPES, default=A)
    scan_frequency = models.PositiveIntegerField(choices=SCAN_FREQUENCY,
                                                 default=WEEKLY)
    next_scan = models.DateTimeField()
    original_filename = models.CharField(max_length=260, null=True, blank=True)  # If type not URL

    def __str__(self):
        return str(self.id) + ': ' + self.type

    def extension(self):
        name, extension = os.path.splitext(self.file.name)
        return extension

    def clean(self):
        # Either URL or File must be entered
        if self.url is None and self.file is None:
            raise ValidationError('URL or file required')


class Invoice(models.Model):
    order = models.ForeignKey(Order)
    price = models.DecimalField(max_digits=9, decimal_places=2)  # 9, 2 = N,NNN,NNN.DD
    explanation = models.CharField(max_length=1000, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    paid = models.DateTimeField(null=True, blank=True)
    is_adjustment = models.BooleanField(default=False)
    # max length is 17: https://developer.paypal.com/docs/classic/api/merchant/TransactionSearch_API_Operation_NVP/
    paypal_tid = models.CharField(max_length=17, null=True, blank=True)

    def __str__(self):
        return str(self.id) + ': ' + str(self.price)


class Query(models.Model):
    query = models.CharField(max_length=250)

    def __str__(self):
        return str(self.id) + ': ' + self.query


class ScanLog(models.Model):
    H = 'H'
    C = 'C'
    FAILED_TYPE = (
        (H, 'HTTP error'),
        (C, 'No content candidates found (initial scan) or matched (post processing)'),
    )

    timestamp = models.DateTimeField(auto_now_add=True)
    protected_resource = models.ForeignKey(ProtectedResource, null=True, blank=True)
    protected_source = models.TextField(null=True, blank=True)  # the text (source) of the protected resource
    queries = models.ManyToManyField(Query, null=True, blank=True)
    scoring_debug = models.TextField(null=True, blank=True)  # TODO Put reasons for scoring each chunk (etc) here
    fail_reason = models.CharField(max_length=500, null=True, blank=True)
    fail_type = models.CharField(max_length=1, choices=FAILED_TYPE, null=True, blank=True)
    user_ip = models.GenericIPAddressField(null=True, blank=True)  # Homepage trials set this, so you cannot (as easily) request results from other users

    def __str__(self):
        return str(self.id) + ': ' + self.timestamp.strftime("%b %d %Y %H:%M:%S")


class ScanResult(models.Model):
    result_log = models.ForeignKey(ScanLog)
    timestamp = models.DateTimeField(auto_now_add=True)
    match_url = models.CharField(max_length=2048)
    match_display_url = models.CharField(max_length=2048)
    match_title = models.CharField(max_length=100)
    match_desc = models.CharField(max_length=500)
    post_scanned = models.BooleanField(default=False)
    post_fail_reason = models.CharField(max_length=500, null=True, blank=True)
    post_fail_type = models.CharField(max_length=1, choices=ScanLog.FAILED_TYPE, null=True, blank=True)
    perc_of_duplication = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # NNN.DD%

    def __str__(self):
        return str(self.id) + ': ' + self.timestamp.strftime("%b %d %Y %H:%M:%S")


class RecentBlogPosts(models.Model):
    title = models.CharField(max_length=200)
    link = models.CharField(max_length=2048)
    desc = models.TextField(null=True, blank=True)
    date = models.DateTimeField()


class UserPreference(models.Model):
    EMAIL_FREQ_INSTANT = 'I'
    EMAIL_FREQ_DAILY = 'D'
    EMAIL_FREQ_WEEKLY = 'W'
    EMAIL_FREQ_MONTHLY = 'M'
    EMAIL_FREQ_NEVER = 'N'
    EMAIL_FREQ = (
        (EMAIL_FREQ_INSTANT, 'Instant'),
        (EMAIL_FREQ_DAILY, 'Daily'),
        (EMAIL_FREQ_WEEKLY, 'Weekly'),
        (EMAIL_FREQ_MONTHLY, 'Monthly'),
        (EMAIL_FREQ_NEVER, 'Never'),
    )

    PER_PAGE_RESULTS = (
        (5, 5),
        (10, 10),
        (15, 15),
        (20, 20),
        (25, 25),
        (30, 30),
        (50, 50),
        (75, 75),
        (100, 100),
        (150, 150),
    )

    user = models.ForeignKey(User)
    results_per_page = models.PositiveSmallIntegerField(choices=PER_PAGE_RESULTS, null=True, blank=True)
    email_frequency = models.CharField(max_length=1, choices=EMAIL_FREQ, null=True, blank=True)
    false_positive_prot = models.BooleanField(default=True)

    def __str__(self):
        return str(self.id)
