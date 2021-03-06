from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns("",
    url(r'^settings$', views.settings, name='user_settings'),
    url(r'^profile$', views.profile, name='user_profile'),
    url(r'^profile/(?P<user_name>\S+)$', views.profile_for_user, name='user_profile_for_user'),
    url(r'^thanksforactivation$', views.thanksforactivation, name="thanksforactivation"),
    url(r"^confirm_email/(?P<key>\w+)/$", views.confirm_email, name="users_confirm_email"),
)


