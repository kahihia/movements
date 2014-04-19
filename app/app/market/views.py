from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from .api.utils import *
from app.market.forms import commentForm
from django.contrib.auth.decorators import login_required
from app.market.models import MarketItem, Notification
from app.market.api.views.market import get_market_json
from django.core.urlresolvers import reverse
from postman.models import Message
from django.db.models import Q

def getUserTags(user):
    all_skills = []
    all_countris = []
    all_issues = []
    if hasattr (user, 'userprofile'):
      all_skills = user.userprofile.skills.all()
      all_countris = user.userprofile.countries.all()
      all_issues = user.userprofile.issues.all()

    return {'skills': [up.pk for up in all_skills],
            'countries': [up.pk for up in all_countris],
            'issues': [up.pk for up in all_issues]}


@login_required
def index(request):
    return render_to_response('market/market.html',
                              {
                                  'title':'Exchange',
                                  'help_text_template': 'market/copy/market_help.html',
                                  'init': 'market',
                                  'tags': getUserTags(request.user)
                                  },
                              context_instance=RequestContext(request))


@login_required
def users(request):
    return render_to_response('market/market.html',
                              {
                                  'title':'Exchangivists',
                                  'help_text_template': 'market/copy/user_help.html',
                                  'init': 'users',
                                  'tags': getUserTags(request.user)
                                  },
                              context_instance=RequestContext(request))


@login_required
def posts(request):
    return render_to_response('market/market.html',
                              {
                                  'title':'My Posts',
                                  'help_text_template': 'market/copy/myposts_help.html',
                                  'init': 'posts',
                                  'tags': getUserTags(request.user)
                                  },
                              context_instance=RequestContext(request))


@login_required
def notifications(request):
    return render_to_response('market/notifications.html',
                              {},
                              context_instance=RequestContext(request))


@login_required
def permanent_delete_postman(request):
    # There is only one row for both users, deleting will delete for both users
    return redirect(reverse('postman_trash'))
    tpks = request.POST.getlist('tpks')
    pks = request.POST.getlist('pks')
    user = request.user
    if pks or tpks:
        filter = Q(pk__in=pks) | Q(thread__in=tpks)
        recipient_rows = Message.objects.as_recipient(user, filter).delete()
        sender_rows = Message.objects.as_sender(user, filter).delete()
    return redirect(reverse('postman_trash'))


@login_required
def postman_unarchive(request):
    tpks = request.POST.getlist('tpks')
    pks = request.POST.getlist('pks')
    user = request.user
    if pks or tpks:
        filter = Q(pk__in=pks) | Q(thread__in=tpks)
        recipient_rows = Message.objects.as_recipient(user, filter).update(**{'recipient_{0}'.format('archived'): False})
        sender_rows = Message.objects.as_sender(user, filter).update(**{'sender_{0}'.format('archived'): False})
        if not (recipient_rows or sender_rows):
            raise Http404  # abnormal enough, like forged ids
    return redirect(reverse('postman_archives'))