from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.models import User
from models import (
    UserProfile, OrganisationalRating, Language, Interest, Region)
from forms import (
    SettingsForm, UserForm, VettingForm, SignUpStartForm, SignupForm,
    MoreAboutYouForm)
from form_overrides import ResetPasswordFormSilent
from allauth.account.views import SignupView, PasswordResetView, PasswordChangeView
from allauth.socialaccount.views import SignupView as SocialSignupView
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import passthrough_next_redirect_url
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.sites.models import Site
from allauth.account.models import EmailConfirmation, EmailAddress
from constance import config
from django.core.urlresolvers import reverse, reverse_lazy
from app.market.api.utils import value
import app.users as users
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
import json
from django.core.mail import EmailMessage
import constance
from django.template.loader import render_to_string
from django.utils import translation
from django.conf import settings as django_settings


def render_settings(request, initial=False):
    template = 'users/user_settings.html'
    user = User.objects.get(pk=request.user.id)
    try:
        settings = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        settings = None
    try:
        perms = request.user.userprofile.notperm
    except:
        perms = {u'experties': u'on',
                 u'bio': u'on',
                 u'resident_country': u'on',
                 u'fb_url': u'on',
                 u'name': u'on',
                 u'linkedin_url': u'on',
                 u'web_url': u'on',
                 u'tweet_url': u'on',
                 u'nationality': u'on',
                 u'occupation': u'on',
                 u'tag_ling': u'on'}

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        if settings:
            settings_form = SettingsForm(request.POST, instance=settings)
        else:
            settings_form = SettingsForm(request.POST)
        if user_form.is_valid() and settings_form.is_valid():
            perms = {k[8:]:v for k, v in request.POST.items() if k.startswith('notperm-')}
            user = user_form.save()
            settings = settings_form.save(commit=False)
            settings.user_id = request.user.id
            settings.notperm = perms
            settings.interface_lang = settings_form.data['interface_lang']
            settings.save()
            settings_form.save_m2m()
            translation.activate(settings_form.data['interface_lang'])
            messages.add_message(request, messages.SUCCESS, 'Profile Update Successfull.')
            if initial:
                template = 'users/welcome.html'
    else:
        user_form = UserForm(instance=request.user)
        settings_form = SettingsForm(instance=settings)

    return render_to_response(template,
                              {
                                'settings_form': settings_form,
                                'user_form': user_form,
                                'notperm': str(perms).replace("u'","'"),
                                'initial': initial,
                                'has_password': user.has_usable_password(),
                                'skills': value('json', users.models.Skills.objects.all()),
                                'issues': value('json', users.models.Issues.objects.all()),
                                'countries': value('json', users.models.Countries.objects.all())
                              },
                              context_instance=RequestContext(request))


@login_required
def initial_settings(request):
    if hasattr(request.user, 'userprofile'):
        return HttpResponseRedirect(reverse('user_settings'))
    return render_settings(request, True)


@login_required
def settings(request):
    from avatar.util import invalidate_cache
    invalidate_cache(request.user)
    return render_settings(request)


@login_required
def profile_for_user(request, user_name):
    return profile(request, user_name)


@login_required
def profile(request, user_name=None):
    if not user_name:
        user = User.objects.get(pk=request.user.id)
    else:
        user = get_object_or_404(User, username=user_name)

    # if the user isn't active, return a 404
    if not user.is_active:
        raise Http404

    try:
        user_profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        user_profile = None
    is_self = False
    if user.id == request.user.id:
        is_self = True
    orate = users.models.OrganisationalRating.objects.filter(user=user).all()
    if len(orate)>0:
        orate = orate[0].rated_by_ahr
    else:
        orate = 0
    return render_to_response('users/user_profile.html',
                                {
                                    'user_details': user,
                                    'user_profile': user_profile,
                                    'is_self': is_self,
                                    'OrganisationalRating': orate
                                },
                                context_instance=RequestContext(request))


def waitforactivation(request):
    return render_to_response('users/waitforactivation.html',
                              {},
                              context_instance=RequestContext(request))


def thanksforactivation(request):
    return render_to_response('users/thanksforactivation.html',
                              {},
                              context_instance=RequestContext(request))


class SilentPasswordResetView(PasswordResetView):
    form_class = ResetPasswordFormSilent
    def form_valid(self, form):
        if form.cleaned_data['email'] == 'silentreject@exchangivist.org':
            return super(PasswordResetView, self).form_valid(form)
        return super(SilentPasswordResetView, self).form_valid(form)

password_reset = SilentPasswordResetView.as_view()


class PasswordChangeViewConf(PasswordChangeView):
    success_url = reverse_lazy("account_change_password_success")

password_change = login_required(PasswordChangeViewConf.as_view())

def password_change_done(request):
    return render_to_response('account/password_change.html',
                              {'message':True},
                              context_instance=RequestContext(request))


def email_doublesignup_upret(self, ret):
    if (ret.has_key('form') and
        ret['form'].errors.has_key('email') and
        ret['form'].errors['email'][0] == u'A user is already registered with this e-mail address.'):
        confem = EmailAddress.objects.filter(email=ret['form'].data['email']).all()
        print confem

        if len(ret['form'].errors)==1:
            self.template_name = "account/verification_sent.html"
        else:
            ret['form'].errors['email'].remove(u'A user is already registered with this e-mail address.')
            if len(ret['form'].errors['email']) == 0:
                ret['form'].errors.pop('email')

        if not confem[0].user.is_active:
            text = render_to_string('emails/notready.html', {})
            subject = render_to_string('emails/notready_subject.html', {})
            email = EmailMessage(subject,
                                 text,
                                 constance.config.NO_REPLY_EMAIL,
                                 [ret['form'].data['email']])
            email.content_subtype = "html"
            email.send()
        else:
            text = render_to_string('emails/securityalert.html', {})
            email = EmailMessage('Security Alert from Movements',
                                 text,
                                 constance.config.NO_REPLY_EMAIL,
                                 [ret['form'].data['email']])
            email.content_subtype = "html"
            email.send()
    return ret


class AhrSocialSignupView(SocialSignupView):
    def get_context_data(self, **kwargs):
        ret = super(AhrSocialSignupView, self).get_context_data(**kwargs)
        context_data = {
            'sign_up': True,
            'post_url': ''
        }
        ret.update(context_data)
        ret = email_doublesignup_upret(self, ret)
        return ret
    template_name = SignupView.template_name

ahr_social_signup = AhrSocialSignupView.as_view()


class AhrSignupView(SignupView):
    form_class = SignupForm

    def get_context_data(self, **kwargs):
        ret = super(SignupView, self).get_context_data(**kwargs)
        context_data = {
            'sign_up': True,
            'post_url': ''
        }
        ret.update(context_data)
        ret = email_doublesignup_upret(self, ret)

        login_url = passthrough_next_redirect_url(self.request,
                                                  reverse("account_login"),
                                                  self.redirect_field_name)
        redirect_field_name = self.redirect_field_name
        redirect_field_value = self.request.REQUEST.get(redirect_field_name)
        ret.update({"login_url": login_url,
                    "redirect_field_name": redirect_field_name,
                    "redirect_field_value": redirect_field_value})
        return ret

process_signup = AhrSignupView.as_view()


def signup_from_home(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('show_market'))
    elif not request.session.get('email') or not \
            request.session.get('password'):
        return HttpResponseRedirect(reverse('signup_start'))

    return render_to_response(
        AhrSignupView.template_name, {
            'form': AhrSignupView.form_class(request.POST or None),
            'post_url': reverse(process_signup),
            'sign_up': True,
        }, context_instance=RequestContext(request))


def signup_start(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('show_market'))

    form = SignUpStartForm(request.POST or None)
    if form.is_valid():
        cleaned_data = form.cleaned_data
        request.session['email'] = cleaned_data['email']
        request.session['password'] = cleaned_data['password1']
        return HttpResponseRedirect(reverse('sign_up'))
    return render_to_response(
        "account/signup_start.html", {'form': form},
        context_instance=RequestContext(request))


def more_about_you(request):
    form = MoreAboutYouForm(request.POST or None,
                            instance=request.user.userprofile)
    if form.is_valid():
        form.save()
        return HttpResponseRedirect(
            request.GET.get('next', reverse('show_market')))
    return render_to_response(
        "users/more_about_you.html",
        {'languages': [(lang.id, lang.name)
                       for lang in Language.objects.all()],
         'interests': [(interest.id, interest.name)
                       for interest in Interest.objects.all()],
         'regions': [(region.id, region.name)
                     for region in Region.objects.all()]},
        context_instance=RequestContext(request))


class AccAdapter(DefaultAccountAdapter):
    def new_user(self, *args, **kwargs):
        user = super(AccAdapter, self).new_user(*args, **kwargs)
        user.is_active = True
        return user

    def send_vetting_email(self, user, form):
        if not config.ACTIVATE_USER_EMAIL:
            raise Exception("Configuration Error: Check that ACTIVATE_USER_EMAIL is set")
        vet_url = reverse('vet_user', args=(user.id,))
        vet_url = 'http://' + Site.objects.get_current().domain + vet_url
        ctx = {
            "user": user,
            "form": form,
            "vet_url": vet_url,
            "current_site": Site.objects.get_current().domain,
        }
        self.send_mail('account/email/user_vetting_email', config.ACTIVATE_USER_EMAIL, ctx)

    def save_user(self, request, user, form, commit=False):
        user = super(AccAdapter, self).save_user(request, user, form, commit)
        user.email = request.session.pop('email')
        user.set_password(request.session.pop('password'))
        user.save()

        # needs to create user and profile in transaction
        # and add profile information from request
        user_profile = UserProfile()
        user_profile.user = user

        user_profile.save()
        self.send_vetting_email(user, form)
        return user

    def get_email_confirmation_redirect_url(self, request):
        super(AccAdapter, self).get_email_confirmation_redirect_url(request)
        key = request.path.split('/')[3]
        conf = EmailConfirmation.objects.filter(key=key)[0]
        user = conf.email_address.user
        if user.is_active:
            return 'http://'+Site.objects.get_current().domain+'/user/thanksforactivation';

        vet_url = reverse('vet_user', args=(user.id,))
        vet_url = 'http://' + Site.objects.get_current().domain + vet_url
        ctx = {
            "user": str(conf.email_address),
            "activate_url": vet_url,
            "vetted": user.is_active,
            "current_site": Site.objects.get_current().domain,
        }

        if not config.ACTIVATE_USER_EMAIL:
            raise Exception("Configuration Error: Check that ACTIVATE_USER_EMAIL is set")

        self.send_mail('account/email/user_confirmed_email', config.ACTIVATE_USER_EMAIL, ctx)
        return 'http://'+Site.objects.get_current().domain+'/user/waitforactivation'


@staff_member_required
def vet_user(request, user_id):
    user = User.objects.get(pk=user_id)
    try:
        rating = OrganisationalRating.objects.get(user=user)
    except OrganisationalRating.DoesNotExist:
        rating = None
    msg = ''
    if request.method == 'POST':
        form = VettingForm(request.POST, instance=rating)
        msg = None
        if form.is_valid():
            if not rating:
                rating = form.save(commit=False)
                rating.user_id = user.id
                rating.save()
            else:
                form.save()
            user.is_active = rating.rated_by_ahr != 0
            user.save()
            typeuser = ContentType.objects.filter(name='user').all()[0]
            log = LogEntry(user_id=request.user.id,
                           content_type= typeuser,
                           object_id=user.id,
                           object_repr=user.username,
                           action_flag=2,
                           change_message="vetted")
            log.save()
            msg = 'User updated'
    else:
        form = VettingForm(instance=rating)
    email_verified = EmailAddress.objects.filter(user=user, verified=True).exists()
    ctx = {
        'email_verified': email_verified,
        'original': user,
        'user': user,
        'form': form,
        'msg': msg,
        'vetted': user.is_active
    }
    return render_to_response('admin/auth/user/vet_user.html', ctx, context_instance=RequestContext(request))


@staff_member_required
def email_vet_user(request, user_id):
    user = User.objects.get(pk=user_id)
    if not user.is_active:
        return  HttpResponse(json.dumps({'success': False, 'message': 'User is not vetted.'}), mimetype="application/json")
    text = render_to_string('emails/getstarted.html',
                            {
                                'user': user,
                                'login_url': 'http://'+Site.objects.get_current().domain+'/accounts/login'
                            }
                        )
    subject = render_to_string('emails/getstarted_subject.html',{})

    email = EmailMessage(subject,
                         text,
                         constance.config.NO_REPLY_EMAIL,
                         [user.email])
    email.content_subtype = "html"
    email.send()
    return HttpResponse(json.dumps({'success': True, 'message': 'An email has been sent to the user.'}), mimetype="application/json")

