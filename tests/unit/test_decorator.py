# encoding: utf-8

from __future__ import absolute_import, unicode_literals

from decimal import Decimal

from django.db.models import Sum
from django.test import TestCase

from tests.proj.myapp.models import Ingredient, Lasagna, Pizza, Salad, Wrap


class BaseDecoratorTestCase(TestCase):
    def setUp(self):
        self.tomato = Ingredient.objects.create(name='tomato', price=Decimal('0.75'))
        self.mozzerella = Ingredient.objects.create(name='mozzarella', price=Decimal('1.50'))
        self.basil = Ingredient.objects.create(name='basil', price=Decimal('0.50'))
        self.cheese = Ingredient.objects.create(name='cheese', price=Decimal('1.00'))
        self.milk = Ingredient.objects.create(name='milk', price=Decimal('0.10'))
        self.beef = Ingredient.objects.create(name='beef', price=Decimal('2.50'))


class DecoratorBasicTests(BaseDecoratorTestCase):
    def setUp(self):
        super(DecoratorBasicTests, self).setUp()
        pizza = Pizza.objects.create(name='margarita', base_price=Decimal('10.00'))
        pizza.ingredients.add(self.tomato)
        pizza.ingredients.add(self.mozzerella)
        pizza.ingredients.add(self.basil)

        self.dish = Pizza.objects.get(pk=pizza.pk)

    def test_call_method_when_uncached(self):
        self.assertIsNone(self.dish._get_price_cached)

        result = self.dish.get_price()
        self.assertNumQueries(1)

        self.assertEqual(result, Decimal('12.75'))
        self.assertEqual(self.dish._get_price_cached, Decimal('12.75'))

    def test_call_method_when_cached(self):
        self.dish._get_price_cached = Decimal('15.00')

        result = self.dish.get_price()
        self.assertNumQueries(0)

        self.assertEqual(result, Decimal('15.00'))

    def test_call_method_caches_after_first_call(self):
        self.assertIsNone(self.dish._get_price_cached)

        self.dish.get_price()
        self.assertNumQueries(1)

        # No new query executed
        self.dish.get_price()
        self.assertNumQueries(1)

    def test_save_updates_empty_cache(self):
        self.assertIsNone(self.dish._get_price_cached)

        self.dish.save()
        # 1 call for the save, 1 for the aggregate within the get_price function.
        self.assertNumQueries(2)

        self.assertEqual(self.dish._get_price_cached, Decimal('12.75'))

    def test_save_updates_filled_cache(self):
        self.dish._get_price_cached = Decimal('15.00')
        self.dish.save()
        # 1 call for the save, 1 for the aggregate within the get_price function.
        self.assertNumQueries(2)

        self.assertEqual(self.dish._get_price_cached, Decimal('12.75'))

    def test_call_method_with_use_dbcache_false(self):
        self.dish._get_price_cached = Decimal('15.00')

        result = self.dish.get_price(use_dbcache=False)
        self.assertNumQueries(1)

        self.assertEqual(result, Decimal('12.75'))
        self.assertEqual(self.dish._get_price_cached, Decimal('12.75'))

    def test_call_method_with_use_dbcache_true(self):
        self.dish._get_price_cached = Decimal('15.00')

        result = self.dish.get_price(use_dbcache=True)
        self.assertNumQueries(0)

        self.assertEqual(result, Decimal('15.00'))
        self.assertEqual(self.dish._get_price_cached, Decimal('15.00'))

    def test_field_orm_usage(self):
        """
        Some tests to see if the ORM can be used with a runtime added field
        like any other field.
        """
        # Just calculate the price.
        self.dish.save()

        pizza_price = Pizza.objects.values_list('_get_price_cached', flat=True)[0]
        self.assertEqual(pizza_price, Decimal('12.75'))

        price_sum = Pizza.objects.aggregate(price_sum=Sum('_get_price_cached'))['price_sum']
        self.assertEqual(price_sum, Decimal('12.75'))


class DecoratorFieldNameTests(BaseDecoratorTestCase):
    def setUp(self):
        super(DecoratorFieldNameTests, self).setUp()
        salad = Salad.objects.create(name='caprese', base_price=Decimal('5'))
        salad.ingredients.add(self.tomato)
        salad.ingredients.add(self.mozzerella)
        salad.ingredients.add(self.basil)

        self.dish = Salad.objects.get(pk=salad.pk)

    def test_field_by_name(self):
        self.assertIsNone(self.dish.price)

        result = self.dish.get_price()
        self.assertNumQueries(1)

        self.assertEqual(result, Decimal('7.75'))
        self.assertEqual(self.dish.price, Decimal('7.75'))


class DecoratorDirtyFuncTests(BaseDecoratorTestCase):
    def setUp(self):
        super(DecoratorDirtyFuncTests, self).setUp()
        lasagna = Lasagna.objects.create(name='classic', base_price=Decimal('8'))
        lasagna.ingredients.add(self.tomato)
        lasagna.ingredients.add(self.mozzerella)
        lasagna.ingredients.add(self.cheese)
        lasagna.ingredients.add(self.milk)

        self.dish = Lasagna.objects.get(pk=lasagna.pk)

    def test_save_when_dirty(self):
        self.assertIsNone(self.dish._get_price_cached)

        result = self.dish.get_price()
        self.assertNumQueries(1)

        self.assertEqual(result, Decimal('11.35'))

        self.dish.base_price = Decimal('9')
        self.dish.save()
        # 1 extra query is needed to recalculate
        self.assertNumQueries(3)

        result = self.dish.get_price()
        self.assertNumQueries(3)

        self.assertEqual(result, Decimal('12.35'))

    def test_save_when_not_dirty(self):
        self.assertIsNone(self.dish._get_price_cached)

        result = self.dish.get_price()
        self.assertNumQueries(1)

        self.assertEqual(result, Decimal('11.35'))

        self.dish.name = 'original'
        self.dish.save()
        # Just the save query is executed, since the get_price method was not
        # considered dirty.
        self.assertNumQueries(2)

        result = self.dish.get_price()
        self.assertNumQueries(2)

        self.assertEqual(result, Decimal('11.35'))


class DecoratorInvalidatedByTests(BaseDecoratorTestCase):
    def setUp(self):
        super(DecoratorInvalidatedByTests, self).setUp()
        wrap = Wrap.objects.create(name='classic', base_price=Decimal('6'))
        wrap.ingredients.add(self.tomato)
        wrap.ingredients.add(self.cheese)
        wrap.ingredients.add(self.beef)

        self.dish = Wrap.objects.get(pk=wrap.pk)

    def test_saving_invalidated_by_model(self):
        self.dish.save()

        self.assertEqual(self.dish._get_price_cached, Decimal('10.25'))
        self.assertEqual(self.dish.get_price(), Decimal('10.25'))

        # Update the related model present in the invalidated_by argument.
        self.beef.price = Decimal('3.00')
        self.beef.save()

        self.dish.refresh_from_db()

        self.assertIsNone(self.dish._get_price_cached)
        self.assertEqual(self.dish.get_price(), Decimal('10.75'))
