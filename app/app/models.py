from django.db.models.signals import post_save
from menu import invalidate_menu_cache

from cms.extensions import PageExtension
from cms.extensions.extension_pool import extension_pool
from django.db import models


class MenuExtension(PageExtension):
    show_on_top_menu = models.BooleanField(default=False)
    show_on_footer_menu = models.BooleanField(default=False)

extension_pool.register(MenuExtension)


def update_menu_settings(sender, **kwargs):
    invalidate_menu_cache()

post_save.connect(update_menu_settings, sender=MenuExtension, dispatch_uid='update_menu_settings')