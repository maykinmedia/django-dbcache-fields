from __future__ import absolute_import, unicode_literals

import logging

from django.db.models.signals import pre_save
from django.utils.module_loading import import_string

from .utils import register

logger = logging.getLogger()


def update_dbcache_fields(sender, instance, **kwargs):
    """
    Update all model fields that are used by dbcache methods by calling their
    original function if flagged as dirty (or no dirty function available).
    """
    if not instance.pk:
        # TODO: We should prolly connect post_save to make sure it gets an initial value.
        return

    sender_class_path = '{}.{}'.format(sender.__module__, sender.__name__)
    for entry in register.get(sender_class_path):
        field_name = entry['field_name']
        func = entry['decorated_method']
        dirty_func = entry['dirty_func']

        # Evaluate dirty function
        if dirty_func is not None:
            try:
                is_dirty = dirty_func(instance, field_name)
            except TypeError:
                raise Exception('The dirty function "{}" should accept at least 2 arguments.'.format(
                    dirty_func.__name__))

            if not is_dirty:
                logger.debug('{}.{} is not marked as dirty.'.format(sender_class_path, field_name))
                continue
            else:
                logger.debug('{}.{} is marked as dirty.'.format(sender_class_path, field_name))

        old_value = getattr(instance, field_name)

        # Update dbcache decorated method field.
        # TODO: Why does this actually not call/use the decorator?
        value = func(instance)
        setattr(instance, field_name, value)
        logger.debug('{}.{} updated from "{}" to "{}".'.format(sender_class_path, field_name, old_value, value))


def clear_dbcache_fields(sender, instance, **kwargs):
    """
    Empty all fields that are invalidated by the save of a related model as
    indicated in the dbcache decorator ``invalidated_by`` argument.
    """
    model_name = '{}.{}'.format(instance._meta.app_label, instance.__class__.__name__)

    # One model can affect multiple other models.
    for class_path, field_names in register.get_model_fields_to_invalidate(model_name).items():
        update_kwargs = dict([(field_name, None) for field_name in field_names])

        model_class = import_string(class_path)
        logger.debug('Saving "{}" (pk={}) triggered the invalidation of "{}" for fields: {}'.format(
            model_name, instance.pk, class_path, ', '.join(field_names)
        ))
        # Set all fields on this model to ``None`` if they are affected by the
        # invalidation.
        model_class.objects.update(**update_kwargs)


def update_models(sender, **kwargs):
    """
    Update the models that have dbcache methods with the proper model fields.
    Also connect the pre-save hook to update fields when needed.
    """
    sender_class_path = '{}.{}'.format(sender.__module__, sender.__name__)
    if sender_class_path not in register:
        return

    # Connect the model to a pre-save hook to update the fields when the
    # instance is saved.
    pre_save.connect(update_dbcache_fields, sender=sender)

    # Update the model definition.
    field_names = []
    for entry in register.get(sender_class_path):
        field = entry['field']
        field_name = entry['field_name']

        # If the field is ``None``, the field was already present on the model.
        if field is not None:
            field.contribute_to_class(sender, field_name)
            field_names.append(field_name)

    logger.debug('{} model was updated with dbcache decorated fields: {}.'.format(
        sender_class_path, ', '.join(field_names)))
