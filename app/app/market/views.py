import json
import urllib

from collections import defaultdict
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext
from django.http import Http404, HttpResponse, HttpResponseRedirect
from app.market.api.utils import HttpResponseForbiden

from app.users.models import Interest, Countries, Issues
from app.utils import form_errors_as_dict
from forms import RequestForm, OfferForm, NewsForm, NewsOfferForm, save_market_item
from models.market import MarketItem, MarketItemViewCounter, MarketItemSalesforceRecord, MarketItemImage, \
    MarketItemDirectOffer


def index(request):
    return index_filter(request, type_filter=None)


def index_filter(request, type_filter):
    if not type_filter in ['request', 'offer']:
        type_filter = ''
    interests = Interest.objects.all()
    issues = Issues.objects.all()
    countries = Countries.objects.select_related('region').all()
    region_dict = {}
    for country in countries:
        if country.region:
            region = country.region
            if region.id in region_dict:
                region_dict[region.id].country_list.append(country)
            else:
                region_dict[region.id] = region
                region.country_list = [country]
    regions = region_dict.values()
    regions = sorted(regions, key=lambda r: r.name)
    return render_to_response('market/market.html',
                              {
                                  'interests': serializers.serialize('json', interests),
                                  'issues': serializers.serialize('json', issues),
                                  'regions': regions,
                                  'countries': countries,
                                  'is_logged_in': request.user.is_authenticated(),
                                  'type_filter': type_filter,
                              },
                              context_instance=RequestContext(request))


def show_post(request, post_id):
    prefetch_list = ['interests', 'issues', 'countries', 'marketitemimage_set', 'marketitemhowcanyouhelp_set', ]
    post = get_object_or_404(MarketItem.objects.defer('comments').prefetch_related(*prefetch_list),
                             pk=post_id,
                             deleted=False,
                             owner__is_active=True)

    if post.is_closed() or not post.published or post.deleted:
        raise Http404('No post matches the given query.')

    countries_to_render = []
    countries = Countries.objects.exclude(region=None).select_related('region').all()
    by_region = defaultdict(list)
    for country in countries:
        by_region[country.region_id].append(country)

    post_countries = post.countries.all()

    if len(post_countries) == len(countries):
        countries_to_render.append('Global')
    else:
        post_countries_by_region = defaultdict(list)
        for country in post_countries:
            post_countries_by_region[country.region_id].append(country)
        for region_id in post_countries_by_region:
            post_region_countries = post_countries_by_region[region_id]
            region_countries = by_region[region_id]
            if len(post_region_countries) == len(region_countries):
                countries_to_render.append(region_countries[0].region.name)
            else:
                for country in post_region_countries:
                    countries_to_render.append(country)
    language_list = []
    translation_languages = []
    translator = False
    if request.user.is_authenticated():
        try:
            __, created = MarketItemViewCounter.objects.get_or_create(viewer_id=request.user.id, item_id=post_id)
            if created:
                MarketItemSalesforceRecord.mark_for_update(post_id)
        except MultipleObjectsReturned:
            pass
        language_list = request.user.userprofile.languages.all()
        translation_languages = list(request.user.userprofile.translation_languages.all())
    if len(translation_languages) > 1:
        for l in translation_languages:
            if l.language_code == post.language:
                translator = True
                break
    if not translator:
        translation_languages = []

    post_data = {
        'post': post,
        'images': post.marketitemimage_set.all(),
        'report_url': reverse('report_post', args=[post.id]),
        'is_logged_in': request.user.is_authenticated(),
        'language_list': language_list,
        'countries_to_render': countries_to_render,

        'translator': translator,
        'translation_languages': json.dumps([{'code': l.language_code, 'name': l.name} for l in translation_languages]),
    }
    news_data = {}
    if post.item_type == MarketItem.TYPE_CHOICES.NEWS:
        news_form = NewsOfferForm(None)
        if request.user.is_authenticated():
            news_form.fields['interests'].initial = request.user.userprofile.interests.values_list('id', flat=True)
        news_data = {
            'news_form': news_form,
            'news_offers': post.get_direct_offers()
        }
    post_data.update(news_data)
    return render_to_response('market/view_post.html', post_data, context_instance=RequestContext(request))


def _create_or_update_post(request, template, form_class, build_redir_url, market_item):
    if market_item:
        form = form_class(request.POST or None, instance=market_item)
    else:
        user_skills = request.user.userprofile.interests.values_list('id', flat=True)
        user_countries = request.user.userprofile.countries.values_list('id', flat=True)
        form = form_class(request.POST or None, user_skills=user_skills, user_countries=user_countries)

    if form.is_valid():
        post = save_market_item(form, request.user)
        if market_item:
            del_ids = []
            for item in request.POST:
                if item.startswith('delete_image_'):
                    img_id = int(item.replace('delete_image_', ''))
                    del_ids.append(img_id)
            MarketItemImage.objects.filter(item=market_item, id__in=del_ids).delete()
        for image in request.FILES:
            MarketItemImage.save_image(post, request.FILES[image])

        # if the user has come directly from the more about you section, then lets save his defaults
        if request.user.userprofile.first_login:
            request.user.userprofile.interests = form.cleaned_data.get('interests')
            request.user.userprofile.countries = form.cleaned_data.get('countries')
            request.user.userprofile.first_login = False
            request.user.userprofile.save()
            request.user.save()

        # user should be added to the requester/provider group depending on the post type
        if post.item_type == MarketItem.TYPE_CHOICES.REQUEST:
            request.user.userprofile.add_to_requesters()
        else:
            request.user.userprofile.add_to_providers()

        redir_url = build_redir_url(post)
        if request.is_ajax():
            return HttpResponse(json.dumps({'success': True, 'redir_url': redir_url}), mimetype="application/json")
        return redirect(redir_url)
    if request.is_ajax():
        errors = form_errors_as_dict(form)
        return HttpResponse(json.dumps({'success': False, 'errors': errors}), mimetype="application/json")
    ctx = {
        'form': form,
        'images': None,
    }
    if market_item:
        ctx['images'] = market_item.marketitemimage_set.all()
    return render_to_response(template, ctx, context_instance=RequestContext(request))


def show_similar_posts(request, post_id):
    post = get_object_or_404(MarketItem.objects.defer('comments'), pk=post_id, deleted=False, owner__is_active=True)
    issues = post.issues.all().values_list('id', flat=True)
    return HttpResponseRedirect(reverse('show_market') + "#{0}".format(urllib.urlencode({'issues': issues}, doseq=True)))


@login_required
def create_offer(request):
    return _create_or_update_post(request,
                                  'market/create_offer.html',
                                  OfferForm,
                                  lambda x: reverse('show_post', args=[x.id]),
                                  None)


@login_required
def create_request(request):
    return _create_or_update_post(request,
                                  'market/create_request.html',
                                  RequestForm,
                                  lambda x: reverse('request_posted'),
                                  None)


@login_required
def create_news(request):
    form = NewsForm(request.POST or None)
    if form.is_valid():
        post = save_market_item(form, request.user)
        news_item = post.generate_news_item(form.cleaned_data.get('news_url'))
        post.title = news_item.title
        post.save()
        related_post_url = form.cleaned_data.get('related_post_url')
        if related_post_url:
            post_id = related_post_url.split('/')[-1]
            post.add_related_post(post_id, request.user)
        return redirect(reverse('show_post', args=[post.id]))
    return render_to_response('market/create_news.html', {'form': form},
                              context_instance=RequestContext(request))


@login_required
def edit_news(request, post_id):
    market_item = get_object_or_404(MarketItem.objects.defer('comments'), pk=post_id)
    if market_item.owner != request.user:
        return HttpResponseForbiden()
    form = NewsForm(request.POST or None, instance=market_item)
    if request.method == 'POST' and form.is_valid():
        save_market_item(form, request.user)
        related_post_url = form.cleaned_data.get('related_post_url')
        if related_post_url:
            post_id = related_post_url.split('/')[-1]
            market_item.add_related_post(post_id, request.user)
        return redirect(reverse('show_post', args=[market_item.id]))
    else:
        form.fields['news_url'].initial = market_item.marketnewsitemdata.original_url
        related_post = market_item.marketitemrelatedpost_set.last()
        if related_post:
            market_item_url = settings.BASE_URL + reverse('show_post', args=[related_post.related_market_item.id])
            form.fields['related_post_url'].initial = market_item_url
    return render_to_response('market/create_news.html', {'form': form, 'news_item': market_item.marketnewsitemdata},
                              context_instance=RequestContext(request))


@login_required
def request_posted(request):
    if request.POST:
        return redirect(reverse('show_market'))
    return render_to_response('market/request_posted.html', {},
                              context_instance=RequestContext(request))


@login_required
def edit_post(request, post_id):
    market_item = get_object_or_404(MarketItem.objects.defer('comments').prefetch_related('marketitemimage_set'),
                                    pk=post_id)
    if market_item.owner != request.user:
        return HttpResponseForbiden()
    if market_item.item_type == MarketItem.TYPE_CHOICES.NEWS:
        return edit_news(request, post_id)
    if market_item.item_type == MarketItem.TYPE_CHOICES.OFFER:
        form_class = OfferForm
        tpl = 'market/create_offer.html'
    else:
        form_class = RequestForm
        tpl = 'market/create_request.html'
    return _create_or_update_post(request,
                                  tpl,
                                  form_class,
                                  lambda x: reverse('show_post', args=[x.id]),
                                  market_item)


@login_required
def notifications(request):
    return render_to_response('market/notifications.html', {},
                              context_instance=RequestContext(request))


@login_required
def permanent_delete_postman(request):
    return redirect(reverse('postman_trash'))


@login_required
def translations(request):
    if not request.user.userprofile.is_translator:
        return redirect(reverse('home'))
    translation_languages = list(request.user.userprofile.translation_languages.all())
    ctx = {
        'translation_languages': json.dumps([{'code': l.language_code, 'name': l.name} for l in translation_languages]),
    }
    return render_to_response('market/translations.html', ctx, context_instance=RequestContext(request))
