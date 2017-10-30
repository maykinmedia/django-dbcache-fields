# encoding: utf-8

from __future__ import absolute_import, unicode_literals

from decimal import Decimal

from django.db.models import Sum
from django.test import TestCase

from tests.proj.myapp.models import Ingredient, Lasagna, Pizza, Salad, Wrap, WrapPromo, WrapType


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

    def test_initial(self):
        # Yup, incorrect but valid for our test case. Adding the ingredients
        # did not invalidate anything.
        self.assertEqual(self.dish._get_price_cached, Decimal('10.00'))

    def test_call_method_when_uncached(self):
        self.dish._get_price_cached = None

        with self.assertNumQueries(2):
            # The cached version is None so:
            # 1 query for the aggregate within the get_price function,
            # 1 query for the update of the cached field.
            result = self.dish.get_price()

        self.assertEqual(result, Decimal('12.75'))
        self.assertEqual(self.dish._get_price_cached, Decimal('12.75'))

    def test_call_method_when_cached(self):
        self.dish._get_price_cached = Decimal('15.00')

        with self.assertNumQueries(0):
            result = self.dish.get_price()

        self.assertEqual(result, Decimal('15.00'))

    def test_call_method_caches_after_first_call(self):
        self.dish._get_price_cached = None

        with self.assertNumQueries(2):
            # The cached version is None so:
            # 1 query for the aggregate within the get_price function,
            # 1 query for the update of the cached field.
            self.dish.get_price()

        with self.assertNumQueries(0):
            # No new query executed, value did not change.
            self.dish.get_price()

    def test_save_updates_empty_cache(self):
        self.dish._get_price_cached = None

        with self.assertNumQueries(3):
            # 1 query for the save,
            # 1 query for the aggregate within the get_price function,
            # 1 query for the update of the cached field.
            self.dish.save()

        self.assertEqual(self.dish._get_price_cached, Decimal('12.75'))

    def test_save_updates_invalid_cache(self):
        self.dish._get_price_cached = Decimal('15.00')

        with self.assertNumQueries(3):
            # 1 query for the save,
            # 1 query for the aggregate within the get_price function,
            # 1 query for the update of the cached field.
            self.dish.save()

        self.assertEqual(self.dish._get_price_cached, Decimal('12.75'))

    def test_save_updates_valid_cache(self):
        self.dish._get_price_cached = Decimal('12.75')

        with self.assertNumQueries(2):
            # 1 call for the save,
            # 1 for the aggregate within the get_price function.
            # none for updating the cached field because the value did not
            # change
            self.dish.save()

        self.assertEqual(self.dish._get_price_cached, Decimal('12.75'))

    def test_call_method_with_use_dbcache_false(self):
        self.dish._get_price_cached = Decimal('15.00')

        with self.assertNumQueries(2):
            # 1 query for the aggregate within the get_price function,
            # 1 query for the update of the cached field.
            result = self.dish.get_price(use_dbcache=False)

        self.assertEqual(result, Decimal('12.75'))
        self.assertEqual(self.dish._get_price_cached, Decimal('12.75'))

    def test_call_method_with_use_dbcache_true(self):
        self.dish._get_price_cached = Decimal('15.00')

        with self.assertNumQueries(0):
            result = self.dish.get_price(use_dbcache=True)  # default

        self.assertEqual(result, Decimal('15.00'))
        self.assertEqual(self.dish._get_price_cached, Decimal('15.00'))

    def test_field_orm_usage(self):
        """
        Some tests to see if the ORM can be used with a runtime added field
        like any other field.
        """
        self.dish.save()

        pizza_price = Pizza.objects.values_list('_get_price_cached', flat=True)[0]
        self.assertEqual(pizza_price, Decimal('12.75'))

        price_sum = Pizza.objects.aggregate(price_sum=Sum('_get_price_cached'))['price_sum']
        self.assertEqual(price_sum, Decimal('12.75'))

    def test_update_on_call_method_when_empty_cache(self):
        self.dish._get_price_cached = None

        with self.assertNumQueries(2):
            # 1 query for the aggregate within the get_price function,
            # 1 query for the update of the cached field.
            self.dish.get_price()

        self.dish.refresh_from_db()
        self.assertEqual(self.dish._get_price_cached, Decimal('12.75'))

    def test_update_on_call_method_when_filled_cache(self):
        self.dish._get_price_cached = Decimal('12.75')

        with self.assertNumQueries(0):
            # no queries, just retrieve from cache even if invalid.
            self.dish.get_price()

        self.dish.refresh_from_db()
        # NOTE: The value is incorrect here, since the price was never updated
        # after adding ingredients. See invalidated_by tests.
        self.assertEqual(self.dish._get_price_cached, Decimal('10.00'))

    def test_cache_update_on_create(self):
        # Not sure if we actually want to update the cached fields after create.
        with self.assertNumQueries(3):
            # 1 call for the create,
            # 1 for the calculating _get_price_cached value,
            # 1 for storing the value in the database, after the creation.
            pizza = Pizza.objects.create(name='hawaii', base_price=Decimal('10.00'))

        # It's on the field
        self.assertEqual(pizza._get_price_cached, Decimal('10.00'))

        # And it's saved in the database.
        pizza.refresh_from_db()
        self.assertEqual(pizza._get_price_cached, Decimal('10.00'))


class DecoratorFieldNameTests(BaseDecoratorTestCase):
    def setUp(self):
        super(DecoratorFieldNameTests, self).setUp()
        salad = Salad.objects.create(name='caprese', base_price=Decimal('5.00'))
        salad.ingredients.add(self.tomato)
        salad.ingredients.add(self.mozzerella)
        salad.ingredients.add(self.basil)

        self.dish = Salad.objects.get(pk=salad.pk)

    def test_initial(self):
        # Yup, incorrect but valid for our test case. Adding the ingredients
        # did not invalidate anything.
        self.assertEqual(self.dish.price, Decimal('5.00'))

    def test_field_by_name(self):
        self.dish.price = None

        with self.assertNumQueries(2):
            # 1 query for the aggregate within the get_price function,
            # 1 query for the update of the cached field.
            result = self.dish.get_price()

        self.assertEqual(result, Decimal('7.75'))
        self.assertEqual(self.dish.price, Decimal('7.75'))


class DecoratorDirtyFuncTests(BaseDecoratorTestCase):
    def setUp(self):
        super(DecoratorDirtyFuncTests, self).setUp()

        # When using the dirty function, the decorated method code should
        # only rely on those things considered by the dirty function. So, no
        # m2m relations here.
        lasagna = Lasagna.objects.create(name='classic', base_price=Decimal('8.00'))

        self.dish = Lasagna.objects.get(pk=lasagna.pk)

    def test_initial(self):
        # Correct and valid, since we did not add any ingredients.
        self.assertEqual(self.dish._get_price_cached, Decimal('8.00'))

    def test_save_when_dirty(self):
        self.dish.base_price = Decimal('9.00')
        with self.assertNumQueries(3):
            # 1 query for the save,
            # 1 query for the aggregate within the get_price function,
            # 1 query for the update of the cached field.
            self.dish.save()

        with self.assertNumQueries(0):
            result = self.dish.get_price()

        self.assertEqual(result, Decimal('9.00'))

    def test_save_when_not_dirty(self):
        self.dish.name = 'original'
        with self.assertNumQueries(1):
            # 1 query for the save.
            # not dirty, so the get_price function is not called and the
            # cached field does not need updating.
            self.dish.save()

        with self.assertNumQueries(0):
            result = self.dish.get_price()

        self.assertEqual(result, Decimal('8.00'))


class DecoratorInvalidatedByTests(BaseDecoratorTestCase):
    def setUp(self):
        # NOTE: This scenario is actually the only full valid scenario since
        # the price depends on related models that invalidate the dish price.
        super(DecoratorInvalidatedByTests, self).setUp()

        self.wrap_type = WrapType.objects.create(type_name='cold', price=Decimal('1.00'))

        wrap = Wrap.objects.create(name='classic', base_price=Decimal('6.00'), wrap_type=self.wrap_type)
        wrap.ingredients.add(self.tomato)  # 0.75
        wrap.ingredients.add(self.cheese)  # 1.00
        wrap.ingredients.add(self.beef)    # 2.50

        self.dish = Wrap.objects.get(pk=wrap.pk)

    def test_initial(self):
        # Cache was invalidated by adding ingredients.
        self.assertIsNone(self.dish._get_price_cached)

    def test_saving_m2m_model_in_invalidated_by(self):
        self.assertEqual(self.beef.price, Decimal('2.50'))
        self.beef.price = Decimal('3.50')
        self.beef.save()

        self.dish.refresh_from_db()

        self.assertIsNone(self.dish._get_price_cached, None)
        self.assertEqual(self.dish.get_price(), Decimal('12.25'))

    def test_adding_m2m_model_in_invalidated_by(self):
        self.assertEqual(self.basil.price, Decimal('0.50'))
        self.dish.ingredients.add(self.basil)

        self.dish.refresh_from_db()

        self.assertIsNone(self.dish._get_price_cached, None)
        self.assertEqual(self.dish.get_price(), Decimal('11.75'))

    def test_removing_m2m_model_in_invalidated_by(self):
        self.assertEqual(self.beef.price, Decimal('2.50'))
        self.dish.ingredients.remove(self.beef)

        self.dish.refresh_from_db()

        self.assertIsNone(self.dish._get_price_cached, None)
        self.assertEqual(self.dish.get_price(), Decimal('8.75'))

    def test_clearing_m2m_model_in_invalidated_by(self):
        self.dish.ingredients.clear()

        self.dish.refresh_from_db()

        self.assertIsNone(self.dish._get_price_cached, None)
        self.assertEqual(self.dish.get_price(), Decimal('7.00'))

    def test_change_fk_model_in_invalidated_by(self):
        self.assertEqual(self.wrap_type.price, Decimal('1.00'))
        self.wrap_type.price = Decimal('2.00')
        self.wrap_type.save()

        self.dish.refresh_from_db()

        self.assertIsNone(self.dish._get_price_cached)
        self.assertEqual(self.dish.get_price(), Decimal('12.25'))

    def test_delete_fk_model_in_invalidated_by(self):
        self.assertEqual(self.wrap_type.price, Decimal('1.00'))
        self.wrap_type.delete()

        self.dish.refresh_from_db()

        self.assertIsNone(self.dish._get_price_cached)
        self.assertEqual(self.dish.get_price(), Decimal('10.25'))

    def test_change_reverse_fk_model_in_invalidated_by(self):
        wrap_promo = WrapPromo.objects.create(wrap=self.dish, promo_price=Decimal('5.00'))

        wrap_promo.promo_price = Decimal('4.00')
        wrap_promo.save()

        self.dish.refresh_from_db()

        self.assertIsNone(self.dish._get_price_cached)
        self.assertEqual(self.dish.get_price(), Decimal('4.00'))

    def test_set_reverse_fk_model_in_invalidated_by(self):
        WrapPromo.objects.create(wrap=self.dish, promo_price=Decimal('5.00'))

        self.dish.refresh_from_db()

        self.assertIsNone(self.dish._get_price_cached)
        self.assertEqual(self.dish.get_price(), Decimal('5.00'))

    def test_delete_reverse_fk_model_in_invalidated_by(self):
        wrap_promo = WrapPromo.objects.create(wrap=self.dish, promo_price=Decimal('5.00'))
        self.dish.save()
        self.dish.refresh_from_db()
        self.assertEqual(self.dish._get_price_cached, Decimal('5.00'))

        wrap_promo.delete()

        self.dish.refresh_from_db()

        self.assertIsNone(self.dish._get_price_cached)
        self.assertEqual(self.dish.get_price(), Decimal('11.25'))
