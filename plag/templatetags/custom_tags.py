import feedparser

from decimal import Decimal

from django import template
from django.templatetags.static import static

from plag.models import ProtectedResource, Order, RecentBlogPosts


register = template.Library()


@register.filter
def friendly_name(user):
    if user.first_name:
        return user.first_name
    else:
        return user.username


@register.filter
def blog_comments(number_of_results):
    return RecentBlogPosts.objects.order_by('-date')[:number_of_results]


@register.filter(name='clickable_prot_res')
def clickable_protected_resource(prot_res):
    if prot_res.type == ProtectedResource.URL:
        url_short = prot_res.url[:50] + '...' if len(prot_res.url) > 50 else prot_res.url
        return '<a href="{0}">{1}</a>'.format(prot_res.url, url_short)
    else:
        if prot_res.type in [ProtectedResource.DOC, ProtectedResource.DOCX]:
            img = '<img src="{0}" />'.format(static('plag/icon/DOC.png'))
        elif prot_res.type == ProtectedResource.PDF:
            img = '<img src="{0}" />'.format(static('plag/icon/PDF.png'))
        elif prot_res.type == ProtectedResource.TXT:
            img = '<img src="{0}" />'.format(static('plag/icon/TXT.png'))
        elif prot_res.type == ProtectedResource.PPTX:
            img = '<img src="{0}" />'.format(static('plag/icon/PPT.png'))

        filename_short = prot_res.original_filename[:50] + '...' if len(
            prot_res.original_filename) > 50 else prot_res.original_filename

        # TODO Change /download path by using equivalent of static import? (if one exists for url, that is?)
        return '{0} <a href="/download/{1}">{2}</a>'.format(img, prot_res.id, filename_short)


@register.filter
def friendly_price(order):
    price = '{0:.2f}'.format(order.price)
    if order.currency == Order.EUR:
        sign = '&#8364;'
    elif order.currency == Order.GBP:
        sign = '&pound;'
    elif order.currency == Order.USD:
        sign = '&dollar;'
    else:
        sign = '&dollar;'
    return sign + price


@register.filter
def invoice_price(invoice):
    price = '{0:.2f}'.format(invoice.price)
    if invoice.order.currency == Order.EUR:
        sign = '&#8364;'
    elif invoice.order.currency == Order.GBP:
        sign = '&pound;'
    elif invoice.order.currency == Order.USD:
        sign = '&dollar;'
    else:
        sign = '&dollar;'
    return sign + price


@register.filter
def get_range(value):
  """
    Filter - returns a list containing range made from given value
    Usage (in template):

    <ul>{% for i in 3|get_range %}
      <li>{{ i }}. Do something</li>
    {% endfor %}</ul>

    Results with the HTML:
    <ul>
      <li>0. Do something</li>
      <li>1. Do something</li>
      <li>2. Do something</li>
    </ul>

    Instead of 3 one may use the variable set in the views
  """
  return range(value)

@register.filter
def get_range_from_one(value):
    return range(1, value)
