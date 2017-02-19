# coding=utf-8

import sys

__all__ = [
    'basestring_type', 'iteritems', 'parse_qs', 'urlsplit', 'urlunsplit'
]

PY3 = sys.version_info >= (3,)

if PY3:
    from urllib.parse import parse_qs, urlsplit, urlunsplit

    basestring_type = str

    def iteritems(d, **kw):
        return d.items(**kw)

else:
    from urlparse import parse_qs, urlsplit, urlunsplit

    basestring_type = basestring

    def iteritems(d, **kw):
        return d.iteritems(**kw)
