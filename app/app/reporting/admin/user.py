# -*- coding: utf-8 -*-
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.db.models import Count, Sum
from django.utils.translation import ugettext_lazy as _
from allauth.account.models import EmailAddress, EmailConfirmation
import csv

from ...market.models import MarketItemViewCounter
from ..models import UserTracking
from .base import TrackingAdmin
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.utils import timezone


class StarRatingListFilter(admin.SimpleListFilter):
    title = _('Movements Rating')
    parameter_name = 'rating'

    def lookups(self, request, model_admin):
        return (
            ('-1', _('Unassigned')),
            ('0', _('0 Stars')),
            ('1', _('1 Star')),
            ('2', _('2 Stars')),
            ('3', _('3 Stars')),
            ('4', _('4 Stars')),
            ('5', _('5 Stars')),
        )

    def queryset(self, request, queryset):
        if self.value() == u'-1':
            return queryset.filter(organisationalrating__rated_by_ahr=None)
        elif self.value():
            return queryset.filter(organisationalrating__rated_by_ahr=self.value())


class EmailVerifiedFilter(admin.SimpleListFilter):
    title = _('Email Verified')
    parameter_name = 'verified'

    def lookups(self, request, model_admin):
        return (
            ('true', _('true')),
            ('false', _('false')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'true':
            return queryset.filter(emailaddress__verified=True)
        if self.value() == 'false':
            return queryset.filter(emailaddress__verified=False)


class UserAdmin(TrackingAdmin):
    list_select_related = ('userprofile', 'organisationalrating', 'emailaddress')
    list_display_links = ('id', 'get_screen_name')
    list_display = (
        'id', 'get_screen_name', 'get_star_rating',
        'get_email_status',  'get_full_name',
        'get_vet_info_count', 'get_resident_country',
        'get_signup_date', 'get_last_login', 'email',
        'get_bio', 'get_fb', 'get_twitter', 'get_linkedin', 'get_website',
        'is_admin',
        #'get_request_count', 'get_offer_count', 'get_comment_count',

    )
    details_display = (
        'id', 'get_screen_name', 'get_movements_rating', 'get_email_status',  'get_full_name',
        'get_nationality', 'get_resident_country',
        'get_signup_date', 'last_login', 'email', 'is_admin',
        'get_fb', 'get_twitter', 'get_linkedin', 'get_website', 'get_bio',
    )
    list_filter = (StarRatingListFilter, EmailVerifiedFilter, )
    change_list_template = 'admin/user_tracking_change_list.html'
    change_form_template = 'admin/user_tracking_change_form.html'
    csv_field_exclude = (
        'is_superuser', 'password', 'username', 'is_staff', 'fullname',
        'is_active', 'first_name', 'last_name')
    csv_safe_fields = csv_field_exclude + (
        'get_full_name', 'email')

    # Prepare fields for change list and CSV.

    def get_screen_name(self, obj):
        return obj.username
    get_screen_name.short_description = _('Screen Name')

    def get_last_login(self, obj):
        return obj.last_login.strftime(self.EXPORT_DATE_FORMAT)
    get_last_login.short_description = _('Last Login')

    def get_signup_date(self, obj):
        return obj.date_joined.strftime(self.EXPORT_DATE_FORMAT)
    get_signup_date.short_description = _('Signup Date')

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = _('Full Name')

    def get_nationality(self, obj):
        if not hasattr(obj, 'userprofile'):
            return _('No profile')
        return obj.userprofile.nationality
    get_nationality.short_description = _('Nationality')

    def get_resident_country(self, obj):
        if hasattr(obj, 'userprofile'):
            return obj.userprofile.resident_country
        return ''
    get_resident_country.short_description = _('Country of Residence')

    def is_admin(self, obj):
        return obj.is_staff
    is_admin.short_description = _('Is Admin')

    def get_request_count(self, obj):
        return obj.request_count
    get_request_count.short_description = _('Request Count')

    def get_offer_count(self, obj):
        return obj.offer_count
    get_offer_count.short_description = _('Offer Count')

    def get_comment_count(self, obj):
        return obj.comment_count
    get_comment_count.short_description = _('Comment Count')

    def get_star_rating(self, obj):
        vet_url = reverse('vet_user', args=(obj.id,))
        stars = obj.star_rating
        if stars == None:
            stars = _('unassigned')
        return u'{0} (<a href="{1}" target="_blank" alt="vet user">{2}</a>)'.format(
            stars, vet_url, _('Rate user'))

    get_star_rating.short_description = _('Movements rating')
    get_star_rating.allow_tags = True
    get_star_rating.admin_order_field = 'star_rating'

    def get_movements_rating(self, obj):
        return obj.star_rating if obj.star_rating else _('unassigned')
    get_movements_rating.short_description = _('Movements Rating')

    def get_fb(self, obj):
        return obj.userprofile.fb_url or _("Not supplied")
    get_fb.short_description = _('Facebook')

    def get_twitter(self, obj):
        return obj.userprofile.tweet_url or _("Not supplied")
    get_twitter.short_description = _('Twitter')

    def get_linkedin(self, obj):
        return obj.userprofile.linkedin_url or _("Not supplied")
    get_linkedin.short_description = _('Linked in')

    def get_website(self, obj):
        return obj.userprofile.web_url or _("Not supplied")
    get_website.short_description = _('Website/blog')

    def get_bio(self, obj):
        return obj.userprofile.bio or _("Not supplied")
    get_bio.short_description = _('Bio')

    def get_vet_info_count(self, obj):
        if not hasattr(obj, 'userprofile'):
            return 0
        count = 0
        if obj.userprofile.fb_url:
            count = count + 1
        if obj.userprofile.tweet_url:
            count = count + 1
        if obj.userprofile.linkedin_url:
            count = count + 1
        if obj.userprofile.web_url:
            count = count + 1
        if obj.userprofile.web_url:
            count = count + 1
        return count
    get_vet_info_count.short_description = _('Count social')

    def get_email_status(self, obj):
        if EmailAddress.objects.filter(verified=True, email=obj.email, user=obj).exists():
            return 'true'
        return 'false'
    get_email_status.short_description = _('Email verified')

    # Overridden methods.
    def changelist_view(self, request, extra_context=None):
        if request.method == 'POST' and '_safe_export' in request.GET:
            return self.export_as_csv(request, safe_mode=True)
        if request.method == 'POST' and '_export_unverified' in request.POST:
            return self.export_unverified(request)
        return super(UserAdmin, self).changelist_view(request, extra_context)

    def render_change_form(self, request, context, add=False, change=False,
                           form_url='', obj=None):
        if obj:
            users = self.make_tracking_queryset(
                self.get_queryset(request).filter(id=obj.id))
            obj = users[0]
            context.update(
                {'report_fields': [
                    (label, self._prep_field(obj, field))
                    for label, field in zip(self._get_labels(self.details_display),
                                            self.details_display)],
                 'obj': obj})
        return super(UserAdmin, self).render_change_form(
            request, context, add, change, form_url, obj)

    def get_queryset(self, request):
        queryset = super(UserAdmin, self).get_queryset(request)
        queryset = queryset.annotate(star_rating=Sum('organisationalrating__rated_by_ahr'))
        return queryset

    # Utils.
    @staticmethod
    def make_tracking_queryset(orig_queryset):
        return orig_queryset
        # queryset = orig_queryset.annotate(
        #     comment_count=Count('comment', distinct=True)
        # )
        # request_count_dict = dict(orig_queryset.filter(
        #     marketitem__item_type='request').annotate(
        #         request_count=Count('marketitem')
        #     ).values_list('id', 'request_count'))
        # offer_count_dict = dict(orig_queryset.filter(
        #     marketitem__item_type='offer').annotate(
        #         offer_count=Count('marketitem')
        #     ).values_list('id', 'offer_count'))
        #
        # users = queryset[:]
        # for user in users:
        #     user.request_count = request_count_dict.get(user.id, 0)
        #     user.offer_count = offer_count_dict.get(user.id, 0)
        # return users

    @staticmethod
    def export_unverified(request):
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=unverified.csv'
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['Name', 'email', 'Date Joined', 'Activation Link'])

        users = get_user_model().objects.filter(emailaddress__verified=False).all()
        for u in users:
            email_address = u.emailaddress_set.filter(primary=True).first()
            if not email_address:
                continue
            confirmation = EmailConfirmation.create(email_address)
            confirmation.sent = timezone.now()
            confirmation.save()
            activate_url = reverse("account_confirm_email", args=[confirmation.key])
            activate_uri = request.build_absolute_uri(activate_url)
            writer.writerow([unicode(u.get_full_name()).encode('utf-8'), u.email, u.date_joined, activate_uri])
        return response

admin.site.register(UserTracking, UserAdmin)
