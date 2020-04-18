Static jQuery
=============

Requirements
------------

`django-appconf`_

`django`_ 1.3 or later

Installation
------------

::

    $ pip install static-jquery
    $ pip install static-jquery==3.2.1.0

Setup
-----

Just add ``'django.contrib.staticfiles'`` and ``'jquery'`` to
INSTALLED\_APPS in your settings.py:

::

    INSTALLED_APPS = (
        # ...
        'django.contrib.staticfiles',
        'jquery',
        # ...
    )

Refer to Django `static files`_ documentation to configure and deploy
static files.

Usage
-----

You can refer to jquery in your template with:

::

    {% load jquery %}
    {% jquery_js %}
    or
    {% jquery_js 3.2.1.0 %}


.. _django: https://www.djangoproject.com/
.. _django-appconf: https://pypi.python.org/pypi/django-appconf/
.. _static files: https://docs.djangoproject.com/en/dev/howto/static-files/



