from django.core.urlresolvers import reverse
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from app.users.models import (
    UserProfile, Countries, Skills, Issues, Nationality, Language, Region,
    Interest, DeleteAccountRequest)
from django.contrib.admin.models import LogEntry
from modeltranslation.admin import TranslationAdmin


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'userprofile'


class MovementsUserAdmin(UserAdmin):
    inlines = (UserProfileInline, )
    list_display = ('username', 'email', 'first_name', 'last_name', 'star_rating', 'rated_by')
    list_filter = UserAdmin.list_filter + ('userprofile__countries', 'userprofile__skills', )

    def star_rating(self, obj):
        try:
            rating = obj.userprofile.ahr_rating
            vet_url = reverse('vet_user', args=(obj.id,))
            return u'{0} (<a href="{1}" target="_blank" alt="vet user">Rate User</a>)'.format(rating, vet_url)
        except:
            return 'No profile'
    star_rating.allow_tags = True

    def vetting(self, obj):
        if obj.is_staff:
            return 'Staff'
        result = 'Vetted' if obj.is_active else 'Not Vetted'
        vet_url = reverse('vet_user', args=(obj.id,))
        return u'<a href="{0}" target="_blank" alt="vet user">Vet User</a> ({1})'.format(vet_url, result)
    vetting.process = 'Process'
    vetting.allow_tags = True

    def rated_by(self, obj):
        log = LogEntry.objects.filter(object_id=obj.id,
                                      change_message="vetted",
                                      action_flag=2).first()
        if log is not None:
            return log.user.username
        else:
            return ''


class SkillsAdmin(TranslationAdmin):
    list_display = ('skills',)


class CountriesAdmin(TranslationAdmin):
    list_display = ('countries',)


class IssuesAdmin(TranslationAdmin):
    list_display = ('issues',)


class NationalityAdmin(TranslationAdmin):
    list_display = ('nationality',)


class NamedObjectAdmin(TranslationAdmin):
    list_display = ('name',)
    list_display_links = list_display


class DeleteAccountRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_of_request')


admin.site.unregister(User)
admin.site.register(DeleteAccountRequest, DeleteAccountRequestAdmin)
admin.site.register(User, MovementsUserAdmin)
admin.site.register(Countries, CountriesAdmin)
admin.site.register(Skills, SkillsAdmin)
admin.site.register(Issues, IssuesAdmin)
admin.site.register(Nationality, NationalityAdmin)
admin.site.register(Language, NamedObjectAdmin)
admin.site.register(Region, NamedObjectAdmin)
admin.site.register(Interest, NamedObjectAdmin)
