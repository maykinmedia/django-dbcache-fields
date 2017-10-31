from __future__ import absolute_import, unicode_literals

import inspect
import logging

logger = logging.getLogger()


class Register(object):
    """
    Central register to keep track of all `dbcache` decorated methods.
    """
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
        """
        Returns a `list` of information about `dbcache` decorated methods.

        :param class_path:
            The `Model` class path.
        :return:
            A `list` of `dict` with the following keys:
                - decorated_method
                - field
                - field_name
                - dirty_func
                - invalidated_by
        """
        return self._model_store.get(class_path, [])

    def get_related_models(self, model):
        """
        Returns a `dict` of models related to the `dbcache` decorated method.
        Typically used to see which models and fields should be invalidated
        when a related model is changed

        :param model:
            The model name in the form `{app label}.{model name}`.
        :return:
            A `dict` where each key is the affected model class path. The
            value is a `list` of field names that are affected.
        """
        return self._invalidation_model_store.get(model, {})

    def __contains__(self, class_path):
        return class_path in self._model_store


def get_class_path(instance):
    """
    Converts an instance or `class` to a class path string.

    :param instance:
        An instance or class.
    :return:
        The stringified class path.
    """
    return '{}.{}'.format(
        instance.__module__,
        instance.__name__ if inspect.isclass(instance) else instance.__class__.__name__)


def get_model_name(instance):
    """
    Converts a `Model` instance or `class` to a model name.

    :param instance:
        A `Model` instance or `class`.
    :return:
        The stringified model name in the form `{app label}.{model name}`.
    """
    return '{}.{}'.format(
        instance._meta.app_label,
        instance.__name__ if inspect.isclass(instance) else instance.__class__.__name__)
