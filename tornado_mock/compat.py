# coding=utf-8

import sys

__all__ = [
    'basestring_type', 'iteritems', 'parse_qs', 'urlsplit', 'urlunsplit', 'StringIO', 'BytesIO'
]

PY3 = sys.version_info >= (3,)

if PY3:
    import http.client as httpcodes
    from io import StringIO, BytesIO
    from urllib.parse import parse_qs, urlsplit, urlunsplit

    unicode_type = str

    def iteritems(d, **kw):
        return d.items(**kw)

else:
    import httplib as httpcodes
    from cStringIO import StringIO
    from urlparse import parse_qs, urlsplit, urlunsplit

    BytesIO = StringIO
    unicode_type = unicode

    def iteritems(d, **kw):
        return d.iteritems(**kw)
