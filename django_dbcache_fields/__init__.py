# -*- coding: utf-8 -*-
"""Django DBCache Fields"""
# :copyright: (c) 2017, Maykin Media BV.
#             All rights reserved.
# :license:   BSD (3 Clause), see LICENSE for more details.

from __future__ import absolute_import, unicode_literals

import re
from collections import namedtuple

from .utils import Register

__version__ = '0.9.2'
__author__ = 'Joeri Bekker'
__contact__ = 'joeri@maykinmedia.nl'
__homepage__ = 'https://github.com/maykinmedia/django-dbcache-fields'
__docformat__ = 'restructuredtext'

# -eof meta-

version_info_t = namedtuple('version_info_t', (
    'major', 'minor', 'patch', 'releaselevel', 'serial',
))

# bumpversion can only search for {current_version}
# so we have to parse the version here.
_temp = re.match(
    r'(\d+)\.(\d+).(\d+)(.+)?', __version__).groups()
VERSION = version_info = version_info_t(
    int(_temp[0]), int(_temp[1]), int(_temp[2]), _temp[3] or '', '')
del(_temp)
del(re)

__all__ = ['register', ]

default_app_config = 'django_dbcache_fields.apps.DBCacheFieldsConfig'

register = Register()
