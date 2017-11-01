from __future__ import absolute_import, unicode_literals

from decimal import Decimal

from django.db import models
from django.db.models import Sum

from django_dbcache_fields.decorators import dbcache


class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=4, decimal_places=2)


class BaseDish(models.Model):
    name = models.CharField(max_length=100)
    base_price = models.DecimalField(max_digits=5, decimal_places=2)
    ingredients = models.ManyToManyField(Ingredient)

    class Meta:
        abstract = True


# Simplistic case
class Drink(models.Model):
    name = models.CharField(max_length=100)
    base_price = models.DecimalField(max_digits=5, decimal_places=2)

    @dbcache(models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True))
    def get_price(self):
        return self.base_price

    # Multiple dbcache decorators on the same Model.
    @dbcache(models.CharField(max_length=100, blank=True, null=True))
    def get_name(self):
        return self.name


# Basic use
class Pizza(BaseDish):

    @dbcache(models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True))
    def get_price(self):
        ingredients_price = self.ingredients.aggregate(total=Sum('price'))['total'] or Decimal()
        return self.base_price + ingredients_price


# Use with dirty_func
def is_base_price_changed(instance, field_name):
    return instance._old_base_price != instance.base_price


class Lasagna(BaseDish):
    def __init__(self, *args, **kwargs):
        super(Lasagna, self).__init__(*args, **kwargs)

        # NOTE: This whole init-method is just for testing the ``dirty_func``
        # argument. It's not mandatory for the workings but a typical use
        # case.
        self._old_base_price = self.base_price

    @dbcache(models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True),
             dirty_func=is_base_price_changed)
    def get_price(self):
        ingredients_price = self.ingredients.aggregate(total=Sum('price'))['total'] or Decimal()
        return self.base_price + ingredients_price


# Use with invalidated_by
class WrapType(models.Model):
    type_name = models.CharField(max_length=100, choices=[('cold', 'cold'), ('hot', 'hot'), ])
    price = models.DecimalField(max_digits=4, decimal_places=2)


class Wrap(BaseDish):
    wrap_type = models.ForeignKey(WrapType, null=True, on_delete=models.SET_NULL)

    # Also intentionally added WrapDemo twice.
    @dbcache(models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True),
             invalidated_by=['myapp.Ingredient', 'myapp.WrapType', 'myapp.WrapPromo', 'myapp.WrapPromo'])
    def get_price(self):
        promo = self.wrappromo_set.first()
        if promo:
            return promo.promo_price

        ingredients_price = self.ingredients.aggregate(total=Sum('price'))['total'] or Decimal()
        type_price = self.wrap_type.price if self.wrap_type else Decimal()
        return self.base_price + type_price + ingredients_price


class WrapPromo(models.Model):
    wrap = models.ForeignKey(Wrap)
    promo_price = models.DecimalField(max_digits=6, decimal_places=2)


# Use with existing field
class Salad(BaseDish):
    price = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)

    @dbcache('price')
    def get_price(self):
        ingredients_price = self.ingredients.aggregate(total=Sum('price'))['total'] or Decimal()
        return self.base_price + ingredients_price
