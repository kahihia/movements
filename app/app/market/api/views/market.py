import json

from app.market.api.utils import *
import app.market as market
from app.market.forms import item_forms, saveMarketItem, QuestionnaireForm
import app.users as users
from django.core import serializers
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404,render_to_response, RequestContext
from django.db.models import Q,Count,Avg
from haystack.views import SearchView
from haystack.query import SearchQuerySet
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.utils.html import escape
from datetime import datetime
from tasks.celerytasks import create_notification, update_notifications, mark_read_notifications, add_view
import constance
import requests
from django.conf import settings
from django.utils.cache import get_cache_key, get_cache
from django.db import connection
from ...models import MarketItem, Questionnaire


cache = get_cache('default')
items_cache = get_cache('items')
user_items_cache = get_cache('user_items')


def get_market_json(objs, request=None):
    alist = []
    for obj in objs:
        alist.append(obj.getdict(request))
    return json.dumps(alist)


def return_item_list(obj, rtype, request=None):
    return HttpResponse(
        get_market_json(obj, request),
        mimetype="application/"+rtype)



@login_required
def add_market_item(request, obj_type, rtype):
    form = item_forms[obj_type](request.POST)
    if form.is_valid():
        obj = saveMarketItem(form, obj_type, request.user)
        create_notification.delay(obj)
        items_cache.clear()
        user_items_cache.clear()
    else:
        return HttpResponseError(json.dumps(get_validation_errors(form)), mimetype="application"+rtype)
    return HttpResponse(json.dumps({ 'success' : True, 'pk':obj.id}),mimetype="application"+rtype)


@login_required
def get_market_item(request, obj_id, rtype):
    retval = cache.get('item-' + obj_id)
    if retval:
        mark_read_notifications.delay((obj_id,),request.user.id)
        return retval
    obj = get_object_or_404(market.models.MarketItem.objects.defer('comments'),
                            Q(exp_date__gte=datetime.now())|Q(never_exp=True),
                            pk=obj_id,
                            deleted=False,
                            owner__is_active=True)
    add_view.delay(obj_id, obj.owner.id, request.user.id)
    mark_read_notifications.delay((obj.id,),request.user.id)
    retval = return_item_list([obj], rtype)
    cache.add('item-' + obj_id, retval)
    return retval

def get_market_item_insecure(request, obj_id, rtype):
    retval = cache.get('item-' + obj_id)
    if retval:
        mark_read_notifications.delay((obj_id,),request.user.id)
        return retval
    obj = get_object_or_404(market.models.MarketItem.objects.defer('comments'),
                            Q(exp_date__gte=datetime.now())|Q(never_exp=True),
                            pk=obj_id,
                            deleted=False,
                            owner__is_active=True)
    add_view.delay(obj_id, obj.owner.id, request.user.id)
    mark_read_notifications.delay((obj.id,),request.user.id)
    retval = return_item_list([obj], rtype)
    cache.add('item-' + obj_id, retval)
    return retval

def getStikies(request, hiddens, sfrom, to):
    sticky_objs = market.models.MarketItemStick.objects.filter(viewer_id=request.user.id)
    if request.GET.get('showHidden', 'false') == 'false':
        sticky_objs  = sticky_objs .filter(~Q(item_id__in=hiddens))
    if request.GET.has_key('types'):
        sticky_objs  = sticky_objs.filter(Q(item__item_type__in=request.GET.getlist('types')))
    sticky_objs = sticky_objs[sfrom:to]
    obj = [i.item for i in sticky_objs]
    return obj


def get_raw(request):
    issues = '(0)'
    countries = '(0)'
    skills = '(0)'
    types = "('offer', 'request')"
    ids= ""
    show_hidden = ""

    if request.GET.has_key('issues'):
        issues = tuple(map(int,request.GET.getlist('issues')))

    if request.GET.has_key('skills'):
        skills = tuple(map(int,request.GET.getlist('skills')))

    if request.GET.has_key('countries'):
        countries = tuple(map(int,request.GET.getlist('countries')))

    if request.GET.has_key('types') and len(request.GET.getlist('types'))>0:
        _req_types = tuple(str(item) for item in request.GET.getlist('types'))
        types = ("%s"%(_req_types,) if len(_req_types)>1 else "('%s')"%(_req_types))

    if request.GET.has_key('search') and request.GET['search']!='':
        objs = SearchQuerySet().models(market.models.MarketItem).filter(text=request.GET['search'])
        _ids= tuple(int(obj.pk) for obj in objs)
        if len(_ids)>0:
            ids = 'AND mi.id IN %s' % _ids if _ids else '(0)'

    if request.GET.get('showHidden', 'false') == 'false':
        show_hidden = 'AND NOT (mi.id IN \
                        (SELECT hiddens."item_id" FROM "market_marketitemhidden" hiddens WHERE hiddens."viewer_id" = \
                        '+str(request.user.id)+'))'

    raw = """
        SELECT mi.*,
               (count(distinct market_marketitem_countries.countries_id) +
               count(distinct market_marketitem_issues.issues_id) +
               count(distinct market_marketitem_skills.skills_id)) as tag_matches
        FROM market_marketitem AS mi
        LEFT JOIN market_marketitem_countries ON
            market_marketitem_countries.marketitem_id = mi.id AND
            market_marketitem_countries.countries_id IN
                """ + "%s" % countries + """
        LEFT JOIN market_marketitem_issues ON
            market_marketitem_issues.marketitem_id = mi.id AND
            market_marketitem_issues.issues_id IN
                """ + "%s" % issues + """
        LEFT JOIN market_marketitem_skills ON
            market_marketitem_skills.marketitem_id = mi.id AND
            market_marketitem_skills.skills_id IN
                """ + "%s" % skills + """
        INNER JOIN "auth_user" ON
            mi.owner_id = "auth_user"."id"
        WHERE
            mi.item_type IN
                """ + types + """
                """ + ids + """
                """ + show_hidden + """ AND
            NOT mi.id IN (
                SELECT stickies."item_id"
                FROM "market_marketitemstick" stickies
                WHERE stickies."viewer_id" = """ + str(request.user.id) + """
            ) AND
            mi.published = True AND
            mi.deleted = False AND
            "auth_user"."is_active" = True AND
            NOT mi.status IN (3, 4) AND
            (
                mi.exp_date >= '""" + str(datetime.now()) + """' OR
                mi.never_exp = True
            )
        GROUP BY mi.id, mi.item_type, mi.owner_id, mi.staff_owner_id, mi.title, mi.details,
            mi.url, mi.published, mi.pub_date, mi.exp_date,
            mi.commentcount, mi.ratecount, mi.reportcount, mi.score, mi.deleted,
            mi.never_exp, mi.status, mi.closed_date, mi.feedback_response

        ORDER BY tag_matches DESC, pub_date DESC
    """
    return raw


@login_required
def get_marketItem_fromto(request, sfrom, to, rtype):
    reqhash = hash(request.path+str(request.GET))
    retval = items_cache.get(reqhash)
    if retval:
        return retval

    query = market.models.MarketItem.objects.raw(get_raw(request))
    stickys = market.models.MarketItemStick.objects.filter(viewer_id=request.user.id).count()
    hiddens = market.models.MarketItemHidden.objects.values_list('item_id', flat=True).filter(viewer_id=request.user.id)
    if stickys >= int(to):
        obj = getStikies(request, hiddens, sfrom, to)
    elif stickys <= int(sfrom):
        obj = query[int(sfrom)-stickys:int(to)-stickys]
    elif stickys >= int(sfrom) and stickys <= int(to):
        sticky_objs = getStikies(request, hiddens, sfrom, stickys)
        market_objs = query[0:(int(to)-stickys)]
        obj = list(sticky_objs)
        b = list(market_objs)
        obj.extend(b)
    retval = return_item_list(obj, rtype, request)
    items_cache.add(reqhash, retval)
    return retval


@login_required
@check_perms_and_get(market.models.MarketItem)
def edit_market_item(request,obj_id,rtype):
    cache.delete('item-'+obj_id)
    cache.delete('translation-'+obj_id)
    items_cache.clear()
    user_items_cache.clear()
    obj = request.obj
    form = item_forms[obj.item_type](request.POST, instance=obj)
    if form.is_valid():
        saveMarketItem(form, obj.item_type, obj.owner)
        update_notifications.delay(obj)
    else:
        return HttpResponseError(json.dumps(get_validation_errors(form)), mimetype="application/"+rtype)
    return HttpResponse(json.dumps({ 'success' : True}),
                        mimetype="application"+rtype)


@login_required
@check_perms_and_get(market.models.MarketItem)
def close_market_item(request, obj_id, rtype):
    cache.delete('item-'+obj_id)
    cache.delete('translation-'+obj_id)
    items_cache.clear()
    user_items_cache.clear()
    market_item = request.obj

    questionnaire = Questionnaire.objects.filter(
        market_type=market_item.item_type).first()

    # Convert questionnaire to json structure.
    questions = [
        {
            'question_id': question.pk,
            'question_text': question.question,
            'question_answer': ''
        } for question in questionnaire.questions.all()
    ]
    data = {'questionnaire': {
        'questionnaire_id': questionnaire.pk,
        'questionnaire_title': questionnaire.title,
        'questions': questions
    }}

    if request.method == 'POST':
        form = QuestionnaireForm(request.POST, questionnaire=questionnaire)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            for question in questions:
                answer = cleaned_data['question_%s' % question['question_id']]
                question['question_answer'] = answer

            market_item.feedback_response = data['questionnaire']
            market_item.status = market_item.STATUS_CHOICES.CLOSED_BY_USER
            market_item.save()

            update_notifications.delay(market_item)
            data = {'success': True}
        else:
            return HttpResponseError(
                json.dumps(get_validation_errors(form)),
                mimetype="application/" + rtype)

    return HttpResponse(
        json.dumps(data), mimetype="application" + rtype)


@login_required
@check_perms_and_get(market.models.MarketItem)
def user_get_marketitem(request, obj_id, rtype):
    return return_item_list([request.obj], rtype)


@login_required
def get_user_marketitem_fromto(request, sfrom, to, rtype):
    reqhash = hash(request.path+str(request.GET))
    retval = user_items_cache.get(reqhash)
    if retval:
        return retval
    query = create_query(request)
    obj = market.models.MarketItem.objects.filter(owner=request.user).filter(query).distinct('id').order_by('-id').defer('comments')[sfrom:to]
    retval = return_item_list(obj, rtype)
    user_items_cache.add(reqhash, retval)
    return retval


@login_required
def get_item_translation(request, obj_id, rtype):
    retval = cache.get('translation-' + obj_id)
    if retval:
        return retval
    obj = get_object_or_404(market.models.MarketItem.objects.defer('comments'),
                            Q(exp_date__gte=datetime.now())|Q(never_exp=True),
                            pk=obj_id,
                            deleted=False,
                            owner__is_active=True)
    resp = requests.get(settings.GOOGLE_TRANS_URL+'key='+constance.config.GOOGLE_API_KEY+'&source=ar&target='+'en'+'&q='+obj.details)
    retval = return_item_list([obj], rtype)
    cache.add('translation-' + obj_id, retval)
    return retval


@login_required
def set_rate(request, obj_id, rtype):
    if not request.POST.has_key('score'):
        return HttpResponseError()
    cache.delete('item-'+obj_id)
    items_cache.clear()
    user_items_cache.clear()
    item = market.models.MarketItem.filter(Q(exp_date__gte=datetime.now())|Q(never_exp=True)).objects.filter(id=obj_id)[0]
    owner = request.user
    rate = market.models.ItemRate.objects.filter(owner=owner).filter(item=item)
    if len(rate)==0:
        rate = market.models.ItemRate(owner=owner, item=item)
    else:
        rate = rate[0]
    rate.score =  int(request.POST['score'])
    rate.save()
    rate.save_base()
    mark_read_notifications.delay((item.id,),request.user.id)
    return HttpResponse(
        json.dumps({'success': 'true',
                    'score':item.score ,
                    'ratecount':item.ratecount
                    }),
        mimetype="application/"+rtype)


@login_required
def get_notifications_fromto(request, sfrom, to, rtype):
    notifications = market.models.Notification.objects.filter(user=request.user.id, item__deleted=False)[sfrom:to]
    alist=[]
    notification_ids=[]
    for notification in notifications:
        alist.append(notification.getDict())
        notification_ids.append(notification.id)
    market.models.Notification.objects.filter(id__in=notification_ids).update(seen=True)
    return HttpResponse(json.dumps({'notifications':alist}),
                        mimetype="application"+rtype)


@login_required
def get_notseen_notifications(request, sfrom, to, rtype):
    notifications = market.models.Notification.objects.filter(user=request.user.id,item__deleted=False).filter(seen=False).only('seen')
    if len(notifications)>0:
        return HttpResponse(json.dumps({'result':True}),
                            mimetype="application"+rtype)
    return  HttpResponse(json.dumps({'result':False}),
                         mimetype="application"+rtype)


@login_required
def get_views_count(request, obj_id, rtype):
    views = market.models.MarketItemViewConter.objects.filter(item_id=obj_id).count()
    return  HttpResponse(json.dumps({'result': views}),
                         mimetype="application"+rtype)


@login_required
def hide_item(request, obj_id, rtype):
    new_hidden = market.models.MarketItemHidden.objects.get_or_create(viewer_id=request.user.id, item_id=obj_id)[0]
    new_hidden.save()
    return  HttpResponse(json.dumps({'result': True}),
                         mimetype="application"+rtype)


@login_required
def unhide_item(request, obj_id, rtype):
    result = False
    hidden = market.models.MarketItemHidden.objects.get(viewer_id=request.user.id, item_id=obj_id)
    if hidden:
        hidden.delete()
        result = True
    return  HttpResponse(json.dumps({'result': result}),
                         mimetype="application"+rtype)


@login_required
def stick_item(request, obj_id, rtype):
    new_sticky = market.models.MarketItemStick.objects.get_or_create(viewer_id=request.user.id, item_id=obj_id)[0]
    new_sticky.save()
    return  HttpResponse(json.dumps({'result': True}),
                         mimetype="application"+rtype)


@login_required
def unstick_item(request, obj_id, rtype):
    result = False
    sticky = market.models.MarketItemStick.objects.get(viewer_id=request.user.id, item_id=obj_id)
    if sticky:
        sticky.delete()
        result = True
    return  HttpResponse(json.dumps({'result': result}),
                         mimetype="application"+rtype)
