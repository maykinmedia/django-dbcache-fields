from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig
from django.db.models.signals import class_prepared, m2m_changed, post_delete, post_save
from django.utils.translation import ugettext_lazy as _

from .receivers import invalidate_dbcache_fields_by_fks, invalidate_dbcache_fields_by_m2m, update_models

__all__ = ['DBCacheFieldsConfig']


class DBCacheFieldsConfig(AppConfig):
    """Default configuration for the django_dbcache_fields app."""

    name = 'django_dbcache_fields'
    label = 'dbcache_fields'
    verbose_name = _('DBCache Fields')

    def ready(self):
        post_save.connect(
            invalidate_dbcache_fields_by_fks,
            dispatch_uid='django_dbcache_fields.receivers.invalidate_dbcache_fields_by_fks__post_save')
        post_delete.connect(
            invalidate_dbcache_fields_by_fks,
            dispatch_uid='django_dbcache_fields.receivers.invalidate_dbcache_fields_by_fks__post_delete')
        m2m_changed.connect(
            invalidate_dbcache_fields_by_m2m,
            dispatch_uid='django_dbcache_fields.receivers.invalidate_dbcache_fields_by_m2m__m2m_changed')


# Connect before this app is ready.
class_prepared.connect(update_models, dispatch_uid='django_dbcache_fields.receivers.update_models')
