from __future__ import absolute_import, unicode_literals

import logging

from django.db.models.signals import post_save
from django.utils.module_loading import import_string

from . import register
from .utils import get_class_path, get_model_name

logger = logging.getLogger(__name__)


def update_dbcache_fields(sender, instance, **kwargs):
    """
    Update all model fields that are used by dbcache methods by calling their
    original function if flagged as dirty (or no dirty function available).
    """
    instance_class_path = get_class_path(instance)
    instance_model_name = get_model_name(instance)

    update_kwargs = {}
    for entry in register.get(instance_class_path):
        field_name = entry['field_name']
        func = entry['decorated_method']
        dirty_func = entry['dirty_func']

        # Evaluate dirty function, if present. If an object was just created,
        # always assume it's dirty.
        if dirty_func is not None and not kwargs.get('created', False):
            is_dirty = dirty_func(instance, field_name)
            if not is_dirty:
                logger.debug('{}.{} is not marked as dirty.'.format(instance_model_name, field_name))
                continue
            else:
                logger.debug('{}.{} is marked as dirty.'.format(instance_model_name, field_name))

        old_value = getattr(instance, field_name)

        # Update dbcache decorated method field.
        # TODO: Why does this actually not call/use the decorator?
        value = func(instance)

        if old_value != value:
            setattr(instance, field_name, value)
            update_kwargs[field_name] = value
            logger.debug('{}.{} updated from "{}" to "{}".'.format(instance_model_name, field_name, old_value, value))
        else:
            logger.debug('{}.{} did not change.'.format(instance_model_name, field_name))

    # If there is something to update, update it in the database.
    if update_kwargs:
        logger.debug('Updating "{}" (pk={}): {}'.format(
            instance_model_name, instance.pk, ', '.join(['{}={}'.format(f, v) for f, v in update_kwargs.items()])
        ))

        instance.__class__.objects.filter(pk=instance.pk).update(**update_kwargs)


def update_models(sender, **kwargs):
    """
    Update the models that have dbcache methods with the proper model fields.
    Also connect the pre-save hook to update fields when needed.
    """
    # The sender is the model that was just prepared.
    sender_class_path = get_class_path(sender)
    sender_model_name = get_model_name(sender)

    if sender_class_path not in register:
        return

    # Connect the model to a post-save hook to update the fields after the
    # model is saved.
    post_save.connect(update_dbcache_fields, sender=sender)

    # Update the model definition.
    field_names = []
    for entry in register.get(sender_class_path):
        field = entry['field']
        field_name = entry['field_name']

        # If the field is `None`, the field should already be present on the model.
        if field is not None:
            # Field name should not exists already, we're adding it.
            field.contribute_to_class(sender, field_name)
            field_names.append(field_name)

    logger.debug('{} model was updated with dbcache decorated fields: {}.'.format(
        sender_model_name, ', '.join(field_names)))


def invalidate_dbcache_fields_by_fks(sender, instance, **kwargs):
    """
    Empty all fields that are invalidated by the save of a related model as
    indicated in the dbcache decorator `invalidated_by` argument.
    """
    instance_model_name = get_model_name(instance)

    # One model can affect multiple other models.
    for class_path, field_names in register.get_related_models(instance_model_name).items():
        update_kwargs = dict([(field_name, None) for field_name in field_names])
        assert update_kwargs, 'There should always be some fields to update'

        model_class = import_string(class_path)
        logger.debug('Saving "{}" (pk={}) triggered the invalidation of "{}" for fields: {}'.format(
            instance_model_name, instance.pk, class_path, ', '.join(field_names)
        ))
        # Set all fields on this model to `None` if they are affected by
        # the invalidation.
        model_class.objects.update(**update_kwargs)


def invalidate_dbcache_fields_by_m2m(sender, instance, action, reverse, model, **kwargs):
    """
    Empty all fields that are invalidated by the save of a related model as
    indicated in the dbcache decorator `invalidated_by` argument.
    """
    # Only act on post-actions.
    if not action.startswith('post_'):
        return

    actions = {
        'post_add': 'Adding',
        'post_remove': 'Removing',
        'poss_clear': 'Clearing',
    }

    instance_class_path = get_class_path(instance)
    model_name = get_model_name(model)

    # One model can affect multiple other models.
    for class_path, field_names in register.get_related_models(model_name).items():
        if instance_class_path == class_path:
            update_kwargs = dict([(field_name, None) for field_name in field_names])
            assert update_kwargs, 'There should always be some fields to update'

            logger.debug('{} "{}" triggered the invalidation of "{}" (pk={}) for fields: {}'.format(
                actions.get(action, action), model, model_name, instance.pk, ', '.join(field_names)
            ))
            # Set all fields on this model to `None` if they are affected
            # by the invalidation.
            instance.__class__.objects.filter(pk=instance.pk).update(**update_kwargs)
