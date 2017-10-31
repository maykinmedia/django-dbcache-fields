==============
Usage examples
==============

Consider the following Django `Model` for a pizza:

.. code-block:: python

    from decimal import Decimal
    from django.db import models
    from django_dbcache_fields.decorators import dbcache

    class Pizza(models.Model):
        TYPES = (
            ('regular', 'regular'),
            ('calzone', 'calzone'),
        )
        name = models.CharField(max_length=100)
        pizza_type = models.CharField(max_length=10, choices=TYPES)
        base_price = models.DecimalField(max_digits=4, decimal_places=2)

    def get_total_price(self):
        supplement = Decimal()
        if self.pizza_type == 'calzone':
            supplement = Decimal(1)

        return self.base_price + supplement


The `get_total_price()` method calculated the final price simply by returning
the `base_price` with a supplement for calzone pizza's.

It's not very exciting nor very computational complex but for the sake of
simplicity, this is our use case.

Every call to `get_total_price()` performs the same calculation over and over
again. Also, you can not simply order the list of pizza's by their total price
(without annotations and conditional expressions) on database level.


Basic usage
===========

Let's decorate the `get_total_price()` function with `dbcache`. To cache the
total price, we need to indicate what type of Django `Field` will be used.

We assume the total price will never exceeds 6 digits, so we'll use a Django
`DecimalField` with the appropriate parameters. The field should always be
allowed to be `null`. For good measure it can also be `blank` in case you add
the field in the Django admin.

.. code-block:: python

    class Pizza(models.Model):
        # ...
        @dbcache(models.DecimalField(max_digits=6, decimal_places=2,
                 blank=True, null=True))
        def get_total_price(self):
            # ...

The total price will now be stored in the database. Under the hood, a new
field was added to the `Pizza` model: `_get_total_price_cached`.

So, our `get_total_price()` function works as it normally would:

.. code-block:: python

    >>> pizza = Pizza.objects.create(
    ...     name='margarita', base_price=Decimal(10), pizza_type='calzone')
    >>> pizza.get_total_price()
    Decimal('11')

In addition, this resulting value is cached on the model field created by the
`dbcache` decorator, which also allows us to perform ORM-operations with it.

.. code-block:: python

    >>> pizza._get_total_price_cached
    Decimal('11')
    >>> Pizza.objects.filter(_get_total_price_cached__gte=Decimal(10))
    <QuerySet [<Pizza: Pizza object>]>

The cached field is updated everytime a new instance is created or when the
instance is saved.

If the cached value is `None`, it's considered to be invalid. As a
consequence, calling the `get_total_price()` method will perform its
calculations as it normally would **and** will update the cached value in the
database (using an update query, so it does not trigger a save signal).


More precise cache invalidation
===============================

In its simplest use case, `dbcache` updates the cached value everytime the
instance is saved or when the decorated function is called and the cached
value is `None`.

Changing the name of a `Pizza` however, will not cause any change to the total
price. For this use case, we can pass a function to the `dbcache` decorator to
indicate whether a change to the instance caused a price change.

Such a *dirty* function can be a very simple function or lambda, and should
accept 2 arguments: The `instance` and the `field_name` of the cached field.

.. code-block:: python

    def is_pizza_price_changed(instance, field_name):
        return instance._original_base_price != instance.base_price

    class Pizza(models.Model):
        def __init__(self, *args, **kwargs)
            super(Pizza, self).__init__(*args, **kwargs)
            # Store the original base price on the instance.
            self._original_base_price = self.base_price
        # ...
        @dbcache(models.DecimalField(max_digits=6, decimal_places=2,
                 blank=True, null=True), dirty_func=is_pizza_price_changed)
        def get_total_price(self):
            # ...

The function `is_pizza_price_changed(...)` is passed to the `dirty_func`
parameter of the `dbcache` decorator. This causes the following behaviour:

.. code-block:: python

    >>> pizza.name = 'hawaii'
    >>> pizza.save()  # The cached field will not be updated
    >>> pizza.get_total_price()
    Decimal('11')

    >>> pizza.base_price = Decimal(5)
    >>> pizza.save()  # The cached field will be updated
    >>> pizza.get_total_price()
    Decimal('6')

    >>> pizza.pizza_type = 'regular'
    >>> pizza.save()  # The cached field will not be updated
    >>> pizza.get_total_price()
    Decimal('11')

Note that in the last example, the total price is **not** correct. The cached
value was not invalidated due to an incomplete *dirty* function. The *dirty*
function should have taken the `pizza_type` into account as well since it can
affect the total price.


Methods that depend on other models
===================================

Consider this slightly altered version of our `Pizza` model. The `pizza_type`
is no longer a choice field but instead a related model: `PizzaType`.

.. code-block:: python

    from django.db import models
    from django_dbcache_fields.decorators import dbcache

    class PizzaType(models.Model):
        name = models.CharField(max_length=100)
        supplement = models.DecimalField(max_digits=4, decimal_places=2)

    class Pizza(models.Model):
        name = models.CharField(max_length=100)
        base_price = models.DecimalField(max_digits=4, decimal_places=2)
        pizza_type = models.ForeignKey(PizzaType)

        @dbcache(models.DecimalField(max_digits=6, decimal_places=2,
                blank=True, null=True), invalidated_by=['myapp.PizzaType'])
        def get_total_price(self):
            return self.base_price + self.pizza_type.supplement

The function `PizzaType` is passed to the `invalidated_by` parameter of the
`dbcache` decorator. Any update to a `PizzaType` will cause all cached
`get_total_price` values to be invalidated.

On the next call of `get_total_price()`, the invalidated cached value will be
updated for this `Pizza` instance. Any save on the instance, would cause the
same update.

Caveat
------
It's worth noting that the value of the `dbcache` generated field can always
be `None`. Be careful when using ORM-functions that rely on a filled value.

Also, a `QuerySet.update()` does not trigger cached field invalidation. In the
above example `PizzaType.objects.update(supplement=Decimal())` will result in
incorrect total prices for pizza's.
