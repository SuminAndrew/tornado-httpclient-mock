# coding=utf-8

from collections import defaultdict
from functools import partial
from string import Template

from tornado.escape import to_unicode, utf8
from tornado.httpclient import HTTPError, HTTPResponse
from tornado.httputil import HTTPHeaders

from tornado_mock.compat import httpcodes, iteritems, parse_qs, unicode_type, urlsplit, urlunsplit, StringIO, BytesIO


def safe_template(format_string, **kwargs):
    """Safe templating using PEP-292 template strings
    (see https://docs.python.org/3/library/string.html#template-strings).

    :param str format_string: a string to be formatted.
    :param kwargs: placeholder values.
    :return str: formatted string.
    """
    return Template(to_unicode(format_string)).safe_substitute(**kwargs)


def patch_http_client(http_client, fail_on_unknown=True):
    """Patches `AsyncHTTPClient` instance to return stub responses.

    :param tornado.httpclient.AsyncHTTPClient http_client: `AsyncHTTPClient` instance.
    :param bool fail_on_unknown: if `True`, any attempt to fetch urls that are not stubbed will
        result in 599 error responses. If `False`, the original `fetch_impl` will be used.
    :return tornado.httpclient.AsyncHTTPClient: patched `AsyncHTTPClient` instance.
    """
    http_client._routes = defaultdict(list)
    old_fetch_impl = http_client.fetch_impl

    def fetch_impl(request, callback):
        def _fetch_mock():
            response_function = _get_route(http_client, request.url, request.method)
            if response_function is not None:
                callback(response_function(request))
                return

            if fail_on_unknown:
                error = HTTPError(599, 'Mock for url {} is not found'.format(request.url))
                callback(get_response_stub(request, code=599, error=error))
            else:
                old_fetch_impl(request, callback)

        http_client.io_loop.add_callback(_fetch_mock)

    http_client.fetch_impl = fetch_impl
    return http_client


def set_stub(http_client, url, request_method='GET',
             response_function=None, response_file=None, response_body='',
             response_code=httpcodes.OK, response_headers=None,
             response_body_processor=safe_template, **kwargs):
    """Set response stub for requested url.

    :param str url: url to be stubbed. Url can contain PEP-292 placeholders
        (see https://docs.python.org/3/library/string.html#template-strings) which will be replaced
        with `kwargs` values.
    :param str request_method: 'GET', 'POST' or any other request method.
    :param callable response_function: function that takes the `HTTPRequest` instance passed to `fetch_impl`
        and must return an instance of `HTTPResponse` instead of making actual HTTP request.
        If `response_function` is defined, all other response_* arguments are ignored.
    :param str response_file: filename containing response body. If `response_file` is specified,
        `response_body` argument is ignored.
    :param str response_body: a string containing response body.
    :param int response_code: response code of the stub response.
    :param dict response_headers: stub response headers.
    :param callable response_body_processor: a function that takes response body
        (loaded from `response_file` or specified in `response_body`) and `kwargs`.
        It can be used to make any kind of modifications to response body, like templating or
        gzipping. By default the same templating function that is used for replacing PEP-292 placeholders
        in `url` is called.
    :param kwargs: parameters that are passed to `url` templating function and to `response_body_processor`.
    """
    url = safe_template(url, **kwargs)

    if response_function is not None:
        _add_route(http_client, url, request_method, response_function)
        return

    if response_file is not None:
        headers = _guess_headers(response_file)
        content = _get_stub(response_file)
    else:
        headers = HTTPHeaders()
        content = response_body

    if callable(response_body_processor):
        content = response_body_processor(content, **kwargs)

    if response_headers is not None:
        headers.update(response_headers)

    def _response_function(request):
        return get_response_stub(
            request, code=response_code, headers=headers, buffer=content, effective_url=url
        )

    _add_route(http_client, url, request_method, _response_function)


def get_response_stub(request, code=httpcodes.OK, **kwargs):
    """A convenient wrapper for generating `tornado.httpclient.HTTPResponse` stubs.
    Method signature is similar to `tornado.httpclient.HTTPResponse` constructor.
    This wrapper automatically converts the value of `buffer` kwarg to `StringIO` instance and
    sets the default `request_time` kwarg value.

    :param tornado.httpclient.HTTPResponse request: incoming request.
    :param code: stub response code.
    :param kwargs: kwargs that are passed to `tornado.httpclient.HTTPResponse` constructor.
    :return:
    """
    kwargs.setdefault('request_time', 1)

    buffer = kwargs.pop('buffer', None)
    buffer = BytesIO(utf8(buffer)) if buffer else None

    return HTTPResponse(request, code, buffer=buffer, **kwargs)


def _guess_headers(fileName):
    if fileName.endswith('.json'):
        return HTTPHeaders({'Content-Type': 'application/json'})
    if fileName.endswith('.xml'):
        return HTTPHeaders({'Content-Type': 'application/xml'})
    if fileName.endswith('.txt'):
        return HTTPHeaders({'Content-Type': 'text/plain'})
    if fileName.endswith('.proto'):
        return HTTPHeaders({'Content-Type': 'application/x-protobuf'})
    return HTTPHeaders()


def _get_route_and_query(url):
    url_parsed = urlsplit(url)
    route = urlunsplit((url_parsed.scheme, url_parsed.netloc, url_parsed.path.strip('/'), '', ''))
    return route, url_parsed.query


def _get_route(http_client, url, request_method):
    route, query = _get_route_and_query(url)
    for dest_method, dest_query, response_function in http_client._routes[route]:
        if dest_method == request_method and _queries_match(dest_query, query):
            return response_function


def _add_route(http_client, url, request_method, response_function):
    route, query = _get_route_and_query(url)
    http_client._routes[route].insert(0, (request_method, query, response_function))


def _get_stub(path):
    with open(path, 'rb') as f:
        return f.read()


def _queries_match(tested_query, request_query):
    a_qs, b_qs = map(partial(parse_qs, keep_blank_values=True), (tested_query, request_query))
    for param, a_value in iteritems(a_qs):
        if param not in b_qs or b_qs[param] != a_value:
            return False

    return True
