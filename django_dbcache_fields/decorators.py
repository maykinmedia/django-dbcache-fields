from __future__ import absolute_import, unicode_literals

import logging

from django.core.exceptions import FieldError
from django.db.models import Field
from django.utils.six import string_types
from qualname import qualname

from . import register

logger = logging.getLogger(__name__)


class dbcache(object):
    """
    Decorate a class method on a Django `Model` to store the result of that
    method in the database.
    """

    def __init__(self, field, field_name=None, dirty_func=None, invalidated_by=None):
        """
        Constructor.

        :param field:
            Django `Model` `Field` instance to store the result.
        :param field_name:
            The field name of the `Field` instance.
        :param dirty_func:
            A function that takes 2 arguments (the `Model` instance and the
            field name) that should return `True` if the field value should
            be recalculated using the original method.
        :param invalidated_by:
            A list of model names in the form `{app_label}.{model name}` that
            when updated, invalidate this field.
        """
        if isinstance(field, string_types):
            if field_name is not None:
                raise ValueError('The dbcache field_name argument must be None when referring to an existing field.')
            field_name = field
            field = None
        else:
            if not isinstance(field, Field):
                raise FieldError(
                    'The dbcache field argument should be a Django Field instance or existing field name')
            elif not field.blank or not field.null:
                raise FieldError('The dbcache field should have blank=True and null=True.')

        if dirty_func and dirty_func.__code__.co_argcount < 2:
            raise TypeError('The dirty function "{}" should accept at least 2 arguments.'.format(dirty_func.__name__))

        self.field = field
        self.field_name = field_name
        self.dirty_func = dirty_func
        self.invalidated_by = invalidated_by

    def __call__(self, f):
        # If there are decorator arguments, __call__() is only called once, as
        # part of the decoration process! You can only give it a single
        # argument, which is the function object.

        # TODO: Check if there are no arguments in the wrapped method

        func_name = f.__name__
        if not self.field_name:
            # TODO: Check if field already exists on model
            field_name = '_{}_cached'.format(func_name)
        else:
            field_name = self.field_name

        # In Python 3: f.__qualname__.split('.')[0]
        class_name = qualname(f).split('.')[0]
        class_path = '{}.{}'.format(f.__module__, class_name)

        register.add(
            class_path, f, self.field, field_name, self.dirty_func, self.invalidated_by
        )

        # Also run on initialization of code
        def wrapped_f(*args, **kwargs):
            if 'use_dbcache' in kwargs:
                use_dbcache = kwargs.pop('use_dbcache')
            else:
                use_dbcache = True

            instance = args[0]

            # If `None` is an actual valid value, this causes the decorated
            # method to always call the original method.
            cached_value = getattr(instance, field_name, None)
            if not use_dbcache or cached_value is None:
                # Call original method.
                value = f(*args, **kwargs)

                logger.debug('{}.{} call returned: {}'.format(
                    class_path, func_name, value
                ))

                if value != cached_value:
                    # Update database field for next call and to store when saved.
                    setattr(instance, field_name, value)
                    logger.debug('{}.{} updated and returned dbcache field ("{}") value: {}'.format(
                        class_path, func_name, field_name, value
                    ))

                    # TODO: Not sure if this is the right approach. Saving
                    # when calling a method is not really nice design.

                    # Update the database only if the instance already has a PK.
                    if instance.pk:
                        logger.debug('{}.{} updated dbcache field ("{}") in the database: {}'.format(
                            class_path, func_name, field_name, value
                        ))
                        # WARNING: This causes a database update query when
                        # calling a method that most likely does not imply
                        # such behaviour (like: Model.get_FOO).
                        #
                        # Bypass triggers by using update
                        instance.__class__.objects.filter(pk=instance.pk).update(**{field_name: value})
            else:
                value = cached_value
                logger.debug('{}.{} returned dbcache field ("{}") value: {}'.format(
                    class_path, func_name, field_name, value
                ))

            return value
        return wrapped_f
