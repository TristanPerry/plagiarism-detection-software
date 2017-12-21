from django.conf.urls import patterns, url

from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

admin.autodiscover()

from plag import views, const

urlpatterns = patterns('',
                       url(r'^$', views.IndexView.as_view(), name='index'),
                       url(r'^index-trial/$', views.IndexTrialView.as_view(), name='index_trial'),

                       url(r'^download/(?P<prot_res_id>\d+)$', views.download_file, name='download'),

                       url(r'^products/$', TemplateView.as_view(template_name='plag/static/products.html'),
                           name='products'),
                       url(r'^features-screenshots/$',
                           TemplateView.as_view(template_name='plag/static/features_and_screenshots.html'),
                           name='features'),
                       url(r'^url-protection/$', TemplateView.as_view(template_name='plag/static/url_protection.html'),
                           name='url_prot'),
                       url(r'^document-protection/$',
                           TemplateView.as_view(template_name='plag/static/doc_protection.html'), name='doc_prot'),
                       url(r'^pricing/$', TemplateView.as_view(template_name='plag/static/pricing.html'),
                           name='pricing'),
                       url(r'^risks-of-plagiarism/$',
                           TemplateView.as_view(template_name='plag/static/risks_of_plagiarism.html'),
                           name='risks_plag'),

                       url(r'^about-us/$', TemplateView.as_view(template_name='plag/static/about.html'), name='about'),
                       url(r'^our-customers/$', TemplateView.as_view(template_name='plag/static/our_customers.html'),
                           name='our_customers'),
                       url(r'^contact-us/$', TemplateView.as_view(template_name='plag/static/contact_us.html'),
                           name='contact'),

                       url(r'^order/$', views.OrderView.as_view(), name='order'),
                       url(r'^ajax/username-check/$', views.username_unique, name='ajax_username_unique'),

                       url(r'^account/$', views.account, name='account'),
                       url(r'^account/profile/$', login_required(views.ProfileView.as_view()), name='profile'),

                       url(r'^account/invoice/(?P<pk>\d+)$', views.invoice, name='invoice'),

                       url(r'^account/invoice/pay/(?P<pk>\d+)$', views.pay_invoice, name='pay_invoice'),
                       url(r'^account/invoice/subscribe/(?P<pk>\d+)$', views.subscribe_invoice,
                           name='subscribe_invoice'),

                       url(r'^ipn-endpoint/$', views.ipn, name='ipn'),

                       url(r'^account/recent-scans/$', views.recent_scans, name='recent_scans_default'),
                       url(r'^account/recent-scans/(?P<num_days>\d+)$', views.recent_scans,
                           name='recent_scans'),
                       url(r'^account/recent-scans/(?P<num_days>\d+)/(?P<hide_zero>hide-zero)$',
                           views.recent_scans, name='recent_scans_hide_zero'),

                       url(r'^account/scan-history/$', views.scan_history, name='scan_history'),
                       url(r'^account/scan-history/(?P<hide_zero>hide-zero)$', views.scan_history,
                           name='scan_history_hide_zero'),

                       url(r'^ajax/plag-results/$', views.plagiarism_results,
                           name='ajax_plag_results_default'),
                       url(r'^ajax/plag-results/(?P<scan_id>\d+)$', views.plagiarism_results,
                           name='plag_results'),

                       url(r'^ajax/sitemap/$', views.sitemap_to_urls, name='ajax_urls'),

                       url(r'^account/protected-resources/$',
                           login_required(views.ProtectedResources.as_view()), name='protected_resources'),

                       url(r'^sitemap/$', TemplateView.as_view(template_name='plag/static/sitemap.html'),
                           name='sitemap'),
                       url(r'^terms-of-service/$',
                           TemplateView.as_view(template_name='plag/static/terms_of_service.html'),
                           name='terms_of_service'),
                       url(r'^privacy-policy/$', TemplateView.as_view(template_name='plag/static/privacy_policy.html'),
                           name='privacy_policy'),

                       # TODO Remove
                       url(r'^data-cleanse/$', views.data_cleanse, name='data_cleanse'),

                       url(r'^copyright/$', TemplateView.as_view(template_name='plag/static/copyright.html'),
                           name='copyright'),
                       url(r'^login/$', 'django.contrib.auth.views.login',
                           {'template_name': 'plag/static/login_error.html'}),
                       url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': 'index'}, name='logout'),
)
