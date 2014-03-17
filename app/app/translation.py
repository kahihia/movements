from modeltranslation.translator import translator, TranslationOptions
from app.users.models import Countries, Skills, Issues, Nationality
from app.editable.models import Placeholder

class CountriesTranslationOptions(TranslationOptions):
    fields = ('countries',)


class NationalityTranslationOptions(TranslationOptions):
    fields = ('nationality',)


class SkillsTranslationOptions(TranslationOptions):
    fields = ('skills',)


class IssuesTranslationOptions(TranslationOptions):
    fields = ('issues',)


class PlaceholderTranslationOptions(TranslationOptions):
    fields = ('content',)


translator.register(Countries, CountriesTranslationOptions)
translator.register(Nationality, NationalityTranslationOptions)
translator.register(Skills, SkillsTranslationOptions)
translator.register(Issues, IssuesTranslationOptions)
translator.register(Placeholder, PlaceholderTranslationOptions)