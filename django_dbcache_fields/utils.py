from __future__ import absolute_import, unicode_literals

import logging

from django.core.exceptions import FieldError
from django.db.models import Field
from django.utils.six import string_types
from qualname import qualname

logger = logging.getLogger()


class Register(object):
    def __init__(self):
        self._model_store = {}
        self._invalidation_model_store = {}

    def add(self, class_path, decorated_method, field, field_name, dirty_func, invalidated_by):
        if class_path not in self._model_store:
            self._model_store[class_path] = []

        entry = {
            'decorated_method': decorated_method,
            'field': field,
            'field_name': field_name,
            'dirty_func': dirty_func,
            'invalidated_by': invalidated_by,
        }
        self._model_store[class_path].append(entry)

        # Store reverse relations for models that invalidate this model.
        if invalidated_by:
            for model in invalidated_by:
                if model not in self._invalidation_model_store:
                    self._invalidation_model_store[model] = {class_path: set()}
                elif class_path not in self._invalidation_model_store[model]:
                    self._invalidation_model_store[model][class_path] = set()
                self._invalidation_model_store[model][class_path].add(field_name)

    def get(self, class_path):
        return self._model_store.get(class_path, [])

    def get_model_fields_to_invalidate(self, model):
        return self._invalidation_model_store.get(model, {})

    def __contains__(self, class_path):
        return class_path in self._model_store


register = Register()


class dbcache(object):

    def __init__(self, field, field_name=None, dirty_func=None, invalidated_by=None):
        """
        Decorate a class method on a Django ``Model`` to store the result of
        that method in the database.

        :param field:
            Django ``Model`` ``Field`` instance to store the result.
        :param field_name:
            The field name of the ``Field`` instance.
        :param dirty_func:
            A function that takes 2 arguments (the ``Model`` instance and the
            field name) that should return ``True`` if the field value should
            be recalculated using the original method.
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

            # If ``None`` is an actual valid value, this causes the decorated
            # method to always call the original method.
            value = getattr(instance, field_name, None)
            if not use_dbcache or value is None:
                # Call original method.
                value = f(*args, **kwargs)

                # Update database field for next call and to store when saved.
                setattr(instance, field_name, value)
                logger.debug('{}.{} updated dbcache field ("{}") and returned actual method value: {}'.format(
                    class_path, func_name, field_name, value
                ))
            else:
                logger.debug('{}.{} returned dbcache field ("{}") value: {}'.format(
                    class_path, func_name, field_name, value
                ))

            return value
        return wrapped_f
