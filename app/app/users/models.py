from json_field import JSONField
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from sorl.thumbnail import ImageField

import uuid

def user_image_upload_path_handler(instance, filename):
    return 'user/img/{file}'.format(file=str(uuid.uuid1())+filename[-4:])

class Skills(models.Model):
	skills = models.CharField(_('skill set'), max_length=255, null=True)

class Issues(models.Model):
	issues = models.CharField(_('issues of interest'), max_length=255, null=True)

class Countries(models.Model):
	countries = models.CharField(_('countries of interest'), max_length=255, null=True)

class Nationality(models.Model):
	nationality = models.CharField(_('nationality'), max_length=255, null=True)

class Residence(models.Model):
	residence = models.CharField(_('country of residence'), max_length=255, null=True)

class UserProfile(models.Model):
	NATIONALITY_CHOICES = (
		('AFG', 'Afganistan'),
		('GBR', 'Great Britain'),
		('EGY', 'Egypt'),
	)
	RESIDENCE_CHOICES = (
		('AFG', 'Afganistan'),
		('GBR', 'Great Britain'),
		('EGY', 'Egypt'),
	)
	user = models.ForeignKey(User)
	image = ImageField(upload_to=user_image_upload_path_handler)
	tag_ling = models.CharField(_('tag line'), max_length=255, null=True, blank=True)
	web_url = models.CharField(_('website url'), max_length=255, null=True, blank=True)
	fb_url = models.CharField(_('facebook page'), max_length=255, null=True, blank=True)
	tweet_url = models.CharField(_('twitter page'), max_length=255, null=True, blank=True)
	occupation = models.CharField(_('occupation'), max_length=255, null=True)
	expertise = models.CharField(_('area of expertise'), max_length=255, null=True, blank=True)
	is_organisation = models.BooleanField(_('organisation'), default=False)
	is_journalist = models.BooleanField(_('journalist'), default=False)
	get_newsletter = models.BooleanField(_('recieves newsletter'), default=False)
	notifications = JSONField(_('notifications'))
	privacy_settings = JSONField(_('privacy settings'))
	nationality = models.CharField(_('nationality'), max_length=3, default=NATIONALITY_CHOICES[0][0], choices=NATIONALITY_CHOICES)
	resident_country = models.CharField(_('country of residence'), max_length=3, default=RESIDENCE_CHOICES[0][0], choices=RESIDENCE_CHOICES)
	skills = models.ManyToManyField(Skills)
	issues = models.ManyToManyField(Issues)
	countries = models.ManyToManyField(Countries)

	def save(self, *args, **kwargs):
		model = self.__class__
		try:
			this = UserProfile.objects.get(id=self.id)
			if this.image != self.image:
				this.image.delete(save=False)
		except:
			return

