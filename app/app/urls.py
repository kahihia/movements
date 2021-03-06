from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

from django.contrib import admin
from app import MovementsAdminSite

from two_factor.urls import urlpatterns as tf_urls
from two_factor.gateways.twilio.urls import urlpatterns as tf_twilio_urls


admin.site = MovementsAdminSite()
admin.autodiscover()

js_info_dict = {
    'packages': ('app',),
}
urlpatterns = patterns(
    '',
    url(r'^$', 'app.views.home', name='home'),
    url(r'^creating-requests$', 'app.views.creating_requests',
        name='creating_requests'),
    url(r'^creating-offers$', 'app.views.creating_offers',
        name='creating_offers'),
    url(r'^get-stats$', 'app.views.get_stats', name='get_stats'),
    url(r'', include('two_factor.urls', 'two_factor')),
    url(r'', include(tf_urls + tf_twilio_urls, 'two_factor')),
    url(r'^google73f6a199341a73ff.html$', 'app.views.youtube_verification', name='youtube_verification'),
    url(r'^google9e5bfcc08bec3049.html$', 'app.views.project_shield_verification', name='project_shield_verification'),
    url(r'^human-rights-support-pro-bono-recognition$', 'app.views.citation', name='citation'),
    url(r'^set-language', 'app.views.set_language', name='set_lang'),

    # public pages
    url(r'^about$', 'app.views.about', name='about'),
    url(r'^team$', 'app.views.team', name='team'),
    url(r'^board$', 'app.views.board', name='board'),
    url(r'^partners$', 'app.views.partners', name='partners'),
    url(r'^faq$', 'app.views.faq', name='faq'),
    url(r'^how-it-works$', 'app.views.how_it_works', name='how_it_works'),
    url(r'^offer-skills$', 'app.views.offer_skills', name='offer_skills'),
    url(r'^request-help$', 'app.views.request_help', name='request_help'),
    url(r'^take-action$', 'app.views.take_action', name='take_action'),



    url(r'^terms-and-conditions$', 'app.views.terms_and_conditions', name='terms_and_conditions'),
    url(r'^contact-us$', 'app.views.contact_us', name='contact_us'),
    url(r'^newsletter-signup$', 'app.views.newsletter_signup', name='newsletter_signup'),

    url(r'^api/login$', 'app.users.views.api_login', name='api_login'),
    url(r'^api/signup-start', 'app.users.views.api_signup_start', name='api_signup_start'),
    url(r'^sign-up-start$', 'app.users.views.signup_start', name="signup_start"),
    url(r'^sign-up$', 'app.users.views.signup_from_home', name="sign_up"),
    url(r'^sign-up/process', 'app.users.views.process_signup', name="process_signup"),
    url(r'^sign-up/more-about-you$', 'app.users.views.more_about_you', name="more_about_you"),
    url(r'^', include('app.market.urls')),

    url(r'^admintinymce/(?P<tinymce_page_detail>[\w.,/_\-]+)/$', 'app.views.tinymce_page'),

    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^unsubscribe$', 'app.users.views.one_click_unsubscribe', {'uuid': None}, name='one_click_unsubscribe'),
    url(r'^unsubscribe/(?P<uuid>.+)$', 'app.users.views.one_click_unsubscribe', name='one_click_unsubscribe'),
    url(r'^unsubscribe-group/(?P<group_id>\d+)$', 'app.users.views.one_click_group_unsubscribe', {'uuid': None}, name='one_click_group_unsubscribe'),
    url(r'^unsubscribe-group/(?P<group_id>\d+)/(?P<uuid>.+)$', 'app.users.views.one_click_group_unsubscribe', name='one_click_group_unsubscribe'),
    url(r'^user/', include('app.users.urls')),
    url(r'^exchange', 'app.views.exchange', name='exchange'),
    url(r'^avatar/render_primary/(?P<user>[\w\@\d\.\-_]{1,30})/(?P<size>[\d]+)/$', 'avatar.views.render_primary',
        name='avatar_render_primary'),
    url(r'^avatar/', include('avatar.urls')),
    url(r'^en/movements/success-stories/(?P<success_story_id>\d+)/$', 'app.views.success_story_item',
        name='success_story_item'),

    url(r'^en/movements/success-stories/(?P<success_story_id>\d+)/next$', 'app.views.success_story_item_next',
        name='success_story_item_next'),

    url(r'^en/movements/success-stories/(?P<success_story_id>\d+)/prev$', 'app.views.success_story_item_prev',
        name='success_story_item_prev'),

    url(r'^en/movements/about-movements/success-stories/(?P<success_story_id>\d+)/$',
        'app.views.success_stories', name='success_stories'),
    # Account View Overrides
    url(r'^accounts/login/+$', 'app.users.views.ratelimited_login', name="account_login"),
    url(r'^accounts/social/signup/+$', 'app.users.views.ahr_social_signup', name="social_sign_up"),
    url(r'^accounts/password/reset/+$', 'app.users.views.password_reset', name="password_reset"),
    url(r"^accounts/password/change/$", 'app.users.views.password_change', name="account_change_password"),
    url(r"^accounts/password/change_done$", 'app.users.views.password_change_done',
        name="account_change_password_success"),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^admin/auth/user/(?P<user_id>\d+)/vet$', 'app.users.views.vet_user', name='vet_user'),
    url(r'^admin/auth/user/(?P<user_id>\d+)/emailvetted$', 'app.users.views.email_vet_user', name='email_vet_user'),
    url(r'^i18n/', include('django.conf.urls.i18n')),


) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.ADMIN_ENABLED:
    urlpatterns += i18n_patterns(
        '',
        url(r'^admin/', include(admin.site.urls)),
        url(r'^rosetta/', include('rosetta.urls')),
    )

urlpatterns += i18n_patterns(
    '',
    url(r'^movements/', include('cms.urls')),
)


if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
                            url(r'^__debug__/', include(debug_toolbar.urls)),
                            )

from .celerytasks import app as celery_app