from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig
from django.db.models.signals import class_prepared, post_save
from django.utils.translation import ugettext_lazy as _

from .receivers import clear_dbcache_fields, update_models

__all__ = ['DBCacheFieldsConfig']


class DBCacheFieldsConfig(AppConfig):
    """Default configuration for the django_dbcache_fields app."""

    name = 'django_dbcache_fields'
    label = 'dbcache_fields'
    verbose_name = _('DBCache Fields')

    def ready(self):
        post_save.connect(clear_dbcache_fields, dispatch_uid='django_dbcache_fields.receivers.clear_dbcache_fields')


# Connect before this app is ready.
class_prepared.connect(update_models, dispatch_uid='django_dbcache_fields.receivers.update_models')
