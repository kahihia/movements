import bleach
import itertools
import logging
import requests
import urllib
import json
from datetime import datetime
from HTMLParser import HTMLParser

from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.utils.html import strip_tags

from app.utils import EnumChoices
from app.market.models.market import MarketItem
from app.market.models.comment import Comment

_logger = logging.getLogger('movements-alerts')


def get_approvable_items_for_profile(profile):
    languages = profile.translation_languages.all()
    market_item_translations = MarketItemTranslation \
        .objects \
        .select_related('market_item') \
        .order_by('-market_item__pub_date', 'language') \
        .filter(get_language_pairing_filter(languages),
                c_status=TranslationBase.inner_state.APPROVAL)
    return market_item_translations


def get_translatable_items_for_profile(profile):
    languages = profile.translation_languages.all()
    status_filter = Q(c_status=TranslationBase.inner_state.NONE) & Q(status=TranslationBase.global_state.PENDING)
    market_item_translations = MarketItemTranslation \
        .objects \
        .select_related('market_item') \
        .order_by('-market_item__pub_date', 'language') \
        .filter(get_language_pairing_filter(languages),
                Q(status_filter) | Q(needs_update=True))
    return market_item_translations


def get_language_pairing_filter(languages):
    pairings = []
    for permutation in itertools.permutations(languages, 2):
        pairings.append(Q(source_language=permutation[0].language_code) & Q(language=permutation[1].language_code))
    language_filter = pairings[0]
    for ix in xrange(1, len(pairings)):
        language_filter = language_filter | pairings[ix]
    return language_filter


def get_or_create_translation(object_id, lang_code, model):
    q = model.objects.filter(status=model.global_state.GOOGLE, **model.get_params(object_id, lang_code))
    translation = q.first()
    if translation is not None:
        return translation
    with transaction.atomic():
        model.get_object_manager().select_for_update().get(pk=object_id)
        translation = q.first()
        if translation is not None:
            return translation
        return model.create_translation(object_id, lang_code)


def get_or_create_user_translation(object_id, lang_code, model):
    q = model.objects.filter(status__gte=model.global_state.PENDING, **model.get_params(object_id, lang_code))
    translation = q.first()
    if translation is not None:
        return translation
    google_translation = get_or_create_translation(object_id, lang_code, model)
    with transaction.atomic():
        model.get_object_manager().select_for_update().get(pk=object_id)
        translation = q.first()
        if translation:
            return translation
        google_translation.pk = None
        google_translation.status = model.global_state.PENDING
        google_translation.save()
        return google_translation


def translate_text(original_text, language):
    success = False
    translation = ""
    source_language = ""
    try:
        api_key = settings.GOOGLE_TRANSLATE_API_KEY
        base_url = settings.GOOGLE_TRANSLATE_BASE
        key = ("key", api_key,)
        query = ("q", unicode(strip_tags(original_text)).encode('utf-8'),)
        target = ("target", language)
        query_string = base_url + urllib.urlencode([key, query, target])
        r = requests.get(query_string)
        if r.status_code == 200:
            data = json.loads(r.content)
            data = data.get("data", {}).get("translations", [])
            if len(data) > 0:
                source_language = data[0].get("detectedSourceLanguage", "")
                translation = data[0].get("translatedText", "")
                if translation:
                    success = True
                    if source_language == language:
                        translation = original_text
                    else:
                        translation = HTMLParser.unescape.__func__(HTMLParser, translation)
    except Exception as ex:
        _logger.exception(ex)
    return success, translation, source_language


def detect_language(text):
    language = "en"
    try:
        key = ("key", settings.GOOGLE_TRANSLATE_API_KEY,)
        query = ("q", unicode(strip_tags(text)).encode('utf-8'),)
        query_string = urllib.urlencode([key, query])
        url = settings.GOOGLE_DETECT_API_URL + query_string
        r = requests.get(url)
        if r.status_code == 200:
            data = json.loads(r.content)
            data = data.get("data", {}).get("detections", [])
            language = data[0][0].get("language", "")
    except Exception as ex:
        _logger.exception(ex)
    return language


class TranslationBase(models.Model):
    class Meta:
        app_label = 'market'
        abstract = True
    _time = settings.COMMENT_TRANSLATION_TIME

    global_state = EnumChoices(
        GOOGLE=(1, _('Google')),
        PENDING=(2, _('Pending a translator')),
        TRANSLATION=(3, _('In translation')),
        DONE=(4, _('Translated')),
    )
    inner_state = EnumChoices(
        NONE=(0, _('None')),
        TRANSLATION=(1, _('In translation')),
        CORRECTION=(2, _('In correction')),
        APPROVAL=(3, _('Waiting for approval')),
    )

    language = models.CharField(_('language'), max_length=10, blank=False)
    source_language = models.CharField(_('source language'), max_length=10, blank=False, default='en')
    details_translated = models.TextField(_('details translated'), blank=False)
    details_candidate = models.TextField(_('details translated candidate'), blank=True)

    generated_at = models.DateField(_('date generated'), auto_now_add=True)
    status = models.PositiveSmallIntegerField(
        _('status'), max_length=1,
        default=global_state.GOOGLE, choices=global_state)
    c_status = models.PositiveSmallIntegerField(
        _('candidate status'), max_length=1,
        default=inner_state.NONE, choices=inner_state)
    owner = models.ForeignKey(
        User, blank=True, null=True)
    owner_candidate = models.ForeignKey(
        User, blank=True, null=True, related_name='%(class)s_candidate')
    created = models.DateTimeField(_('date generated'), auto_now_add=True)
    edited = models.DateTimeField(_('date edited'), auto_now=True)
    timer = models.DateTimeField(_('date edited'), null=True)
    needs_update = models.BooleanField(_('Needs update'), default=False)

    def is_active(self, user):
        return user == self.owner_candidate and \
            self.c_status in (self.inner_state.TRANSLATION, self.inner_state.CORRECTION)

    def is_done(self):
        return self.status == self.global_state.DONE

    def clear_state(self, save=True):
        if not self.is_done():
            self.status = self.global_state.PENDING
        self.c_status = self.inner_state.NONE
        self.owner_candidate = None
        self.timer = None
        self.details_candidate = ''
        if save:
            self.save()

    def get_translated_data(self):
        return {'details_translated': bleach.clean(self.details_translated, strip=True),
                'source_language': self.source_language,
                'username': self.owner.username if self.status == self.global_state.DONE else 'Google'}

    def get_init_data(self, user):
        active = self.is_active(user)
        return {'correction': self.is_done(),
                'prev_text': self.details_translated,
                'active': active,
                'error': None,
                'other_user_editing': False,
                'owner': self.owner_candidate.username if self.owner_candidate else None,
                'owner_url': reverse('user_profile_for_user', args=(self.owner_candidate.username,)) if self.owner_candidate else None,
                'status': self.c_status,
                'details_translated': self.details_candidate,
                'save_draft_url': self.save_draft_url(),
                'put_back_to_edit_url': self.put_back_to_edit_url(),
                'take_off': self.take_off_url(),
                'done_url': self.done_url()}

    def get_endtime(self):
        # TODO need to move timings to settings
        if self.c_status == self.inner_state.TRANSLATION:
            return self.timer + self._time
        elif self.c_status == self.inner_state.CORRECTION:
            return self.edited + self._time / 2
        return None

    def save_draft(self, data):
        self.details_candidate = data.get('details_translated', '')
        self.save()

    def set_done(self, data):
        self.details_candidate = data.get('details_translated', '')
        self.timer = None
        self.c_status = self.inner_state.APPROVAL
        self.save()

    def approve(self, data):
        self.owner = self.owner_candidate
        self.status = self.global_state.DONE
        self.details_translated = data.get('details_translated', self.details_candidate)

    def take_in(self, user):
        self.owner_candidate = user
        self.timer = datetime.utcnow()
        if not self.is_done():
            self.status = self.global_state.TRANSLATION
            self.c_status = self.inner_state.TRANSLATION
        else:
            self.c_status = self.inner_state.CORRECTION
        self.details_candidate = self.details_translated
        self.save()

    def set_to_edit(self):
        if not self.is_done():
            self.status = self.global_state.TRANSLATION
            self.c_status = self.inner_state.TRANSLATION
        else:
            self.c_status = self.inner_state.CORRECTION
        self.save()

    def has_perm(self, user, target_lang):
        if user.userprofile.is_cm:
            return True
        rates = user.userprofile.translation_languages.filter(launguage_code__in=[self.source_language, target_lang])
        return rates.count() == 2

    def make_url(self, key):
        return reverse('translation:comment:' + key, args=[self.comment_id])

    def take_in_url(self):
        return self.make_url('take_in')

    def save_draft_url(self):
        return self.make_url('save_draft')

    def put_back_to_edit_url(self):
        return self.make_url('put_back_to_edit')

    def take_off_url(self):
        return self.make_url('take_off')

    def done_url(self):
        return self.make_url('done')

    def approval_url(self):
        return self.make_url('approve')

    def revoke_url(self):
        return self.make_url('revoke')

    def correction_url(self):
        return self.make_url('corrections')

    def cm_urls_dict(self):
        return {'approval_url': self.approval_url() if self.c_status == self.inner_state.APPROVAL else None,
                'revoke_url': self.revoke_url() if self.c_status == self.inner_state.APPROVAL else None,
                'correction_url': self.correction_url() if self.c_status == self.inner_state.APPROVAL else None,
                }


class MarketItemTranslation(TranslationBase):
    _time = settings.POST_TRANSLATION_TIME

    market_item = models.ForeignKey(
        MarketItem, verbose_name=_('market item'))
    title_translated = models.TextField(_('title translated'), blank=False)
    title_candidate = models.TextField(_('title translated candidate'), blank=True)

    def clear_state(self, save=True):
        self.title_candidate = ''
        super(MarketItemTranslation, self).clear_state(save)

    @staticmethod
    def get_params(object_id, lang_code):
        return {'market_item_id': object_id, 'language': lang_code}

    @staticmethod
    def get_object(object_id):
        return MarketItem.objects.get(pk=object_id)

    @staticmethod
    def get_object_manager():
        return MarketItem.objects

    @staticmethod
    def get_original(item):
        return {
            'title_translated': bleach.clean(item.title, strip=True),
            'details_translated': bleach.clean(item.details, strip=True),
        }

    @staticmethod
    def create_translation(object_id, lang_code):
        try:
            market_item = MarketItem.objects.get(pk=object_id)
        except MarketItem.DoesNotExist:
            return None
        else:
            success, title_translation, source_lang = translate_text(market_item.title, lang_code)
            if success:
                success, details_translation, source_lang = translate_text(market_item.details, lang_code)
            if success:
                translation = MarketItemTranslation.objects.create(
                    market_item=market_item,
                    title_translated=title_translation,
                    details_translated=details_translation,
                    language=lang_code,
                    source_language=source_lang)
                return translation
        return MarketItemTranslation.objects.create(
            market_item=market_item,
            title_translated=market_item.title,
            details_translated=u'Google Translation Failed',
            language=lang_code,)

    def get_translated_data(self):
        data = super(MarketItemTranslation, self).get_translated_data()
        data.update({
            'title_translated': bleach.clean(self.title_translated, strip=True)})
        return data

    def get_init_data(self, user):
        data = super(MarketItemTranslation, self).get_init_data(user)
        data.update({'prev_title': self.title_translated,
                     'title_translated': self.title_candidate})
        return data

    def set_done(self, data):
        self.title_candidate = data.get('title_translated', '')
        super(MarketItemTranslation, self).set_done(data)

    def save_draft(self, data):
        self.title_candidate = data.get('title_translated', '')
        super(MarketItemTranslation, self).save_draft(data)

    def approve(self, data):
        self.title_translated = data.get('title_translated', self.title_candidate)
        super(MarketItemTranslation, self).approve(data)

    def take_in(self, user):
        self.title_candidate = self.title_translated
        super(MarketItemTranslation, self).take_in(user)

    def make_url(self, key):
        return reverse('translation:market:' + key, args=[self.market_item_id])


class CommentTranslation(TranslationBase):
    comment = models.ForeignKey(Comment, verbose_name=_('comment'))

    @staticmethod
    def get_params(object_id, lang_code):
        return {'comment_id': object_id, 'language': lang_code}

    @staticmethod
    def get_object(object_id):
        return Comment.objects.get(pk=object_id)

    @staticmethod
    def get_object_manager():
        return Comment.objects

    @staticmethod
    def get_original(item):
        return {
            'details_translated': bleach.clean(item.contents, strip=True),
        }

    @staticmethod
    def create_translation(object_id, lang_code):
        try:
            comment = Comment.objects.get(pk=object_id)
        except Comment.DoesNotExist:
            return None
        else:
            success, details_translation, source_lang = translate_text(comment.contents, lang_code)
            if success:
                translation = CommentTranslation.objects.create(
                comment=comment,
                details_translated=details_translation,
                language=lang_code,
                source_language=source_lang)
                return translation
        return None
