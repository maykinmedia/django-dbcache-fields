=========================
DBCache Fields for Django
=========================

:Version: 0.9.0
:Download: https://pypi.python.org/pypi/django_dbcache_fields
:Source: https://github.com/maykinmedia/django-dbcache-fields
:Keywords: django, database, cache, methods, decorator

|build-status| |coverage|

About
=====

This library provides a decorator ``dbcache`` that caches the result of your
Django ``Model`` methods in your database.

It adds a regular ``Field`` on your ``Model`` for each method that you
decorate. This means you can use all ORM-functions like aggregation and
migrations. You can use existing fields or let ``dbcache`` create the field
for you.

You can also invalidate the cached value by creating a _dirty_ function or by
indicating which other models affect the this cached value. By default, the
cached value is only updated when the model is saved.

Installation
============

You can install django_dbcache_fields either via the Python Package Index
(PyPI) or from source.

To install using `pip`,:

.. code-block:: console

    $ pip install -U django_dbcache_fields

Usage
=====

To use this with your project you need to follow these steps:

#. Install the django_dbcache_fields library:

   .. code-block:: console

      $ pip install django_dbcache_fields

#. Add ``django_dbcache_fields`` to ``INSTALLED_APPS`` in your Django
   project's ``settings.py``::

    INSTALLED_APPS = (
        ...,
        'django_dbcache_fields',
    )

   Note that there is no dash in the module name, only underscores.

#. All done. You can now decorate methods in your ``Model``s with
   ``@dbcache``.

Example
=======

Simple example to show what ``dbcache`` does::

    from django.db import models
    from django_dbcache_fields.utils import dbcache

    class Ingredient(models.Model):
        name = models.CharField(max_length=100)
        price = models.DecimalField(max_digits=4, decimal_places=2)

    class Pizza(models.Model):
        name = models.CharField(max_length=100)
        ingredients = models.ManyToManyField(Ingredient)

        @dbcache(models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True))
        def get_price(self):
            return self.ingredients.aggregate(total=Sum('price'))['total'] or Decimal()

Every call to ``get_price`` would normally perform a database query to
calculate the total price of all ingredients. However, the ``dbcache``
decorator caused a new field to be added to the model: A ``DecimalField`` that
can store the resulting value of the ``get_price`` function, so it doesn't
need to perform the same query over and over again.


.. |build-status| image:: https://secure.travis-ci.org/maykinmedia/django-dbcache-fields.svg?branch=master
    :alt: Build status
    :target: https://travis-ci.org/maykinmedia/django-dbcache-fields

.. |coverage| image:: https://codecov.io/github/maykinmedia/django-dbcache-fields/coverage.svg?branch=master
    :target: https://codecov.io/github/maykinmedia/django-dbcache-fields?branch=master
