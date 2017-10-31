# encoding: utf-8

from __future__ import absolute_import, unicode_literals

from django.core.exceptions import FieldError
from django.db import models
from django.test import TestCase

from django_dbcache_fields.decorators import dbcache


class DecoratorTestCase(TestCase):
    def test_raise_exc_for_args_field_by_name_and_fieldname(self):
        self.assertRaises(ValueError, dbcache, 'foo', field_name='bar')

    def test_raise_exc_for_invalid_field(self):
        self.assertRaises(FieldError, dbcache, object())

    def test_raise_exc_for_field_without_blank_or_null(self):
        self.assertRaises(FieldError, dbcache, models.IntegerField(blank=False, null=False))
        self.assertRaises(FieldError, dbcache, models.IntegerField(blank=True, null=False))
        self.assertRaises(FieldError, dbcache, models.IntegerField(blank=False, null=True))

    def test_raise_exc_for_invalid_dirty_func(self):
        self.assertRaises(TypeError, dbcache, 'foo', dirty_func=lambda x: True)
