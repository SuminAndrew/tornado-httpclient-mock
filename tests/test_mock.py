# coding=utf-8

from tornado.httpclient import AsyncHTTPClient
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application, asynchronous, RequestHandler

from tornado_mock.httpclient import get_response_stub, patch_http_client, set_stub


class TestHandler(RequestHandler):
    @asynchronous
    def get(self, *args, **kwargs):
        def callback(response):
            self.write('{} : '.format(response.code))
            if 'Content-Type' in response.headers:
                self.write('{} : '.format(response.headers.get('Content-Type')))
            self.finish(response.body)

        self_uri = 'http://' + self.request.host + self.request.path
        self.application.http_client.fetch(self_uri + '?arg1=val1&arg2=val2', method='POST', body='', callback=callback)

    def post(self, *args, **kwargs):
        self.write('NO MOCK')
        self.set_header('Content-Type', 'text/html')


class _BaseHTTPClientMockTest(AsyncHTTPTestCase):
    def get_app(self):
        app = Application([
            ('/simple_fetch', TestHandler)
        ])

        self.app_http_client = app.http_client = self.get_app_http_client()
        return app

    def get_app_http_client(self):
        raise NotImplementedError()

    def test_missing_mock_fail_on_unknown_true(self):
        patch_http_client(self.app_http_client)

        set_stub(
            self.app_http_client, self.get_url('/simple_fetch?arg1=val1&arg2=val2&arg3=val3'), request_method='POST',
            response_body='GET MOCK'
        )

        response = self.fetch('/simple_fetch')
        self.assertEqual(response.body, b'599 : ')

    def test_not_matching_mock(self):
        patch_http_client(self.app_http_client)

        response = self.fetch('/simple_fetch')
        self.assertEqual(response.body, b'599 : ')

    def test_missing_mock_fail_on_unknown_false(self):
        patch_http_client(self.app_http_client, fail_on_unknown=False)

        response = self.fetch('/simple_fetch')
        self.assertEqual(response.body, b'200 : text/html : NO MOCK')

    def test_mock_response_body(self):
        patch_http_client(self.app_http_client)

        # Test that mock for GET request is not used
        set_stub(
            self.app_http_client, self.get_url('/simple_fetch?arg1=val1'), response_body='GET MOCK'
        )

        set_stub(
            self.app_http_client, self.get_url('/simple_fetch?arg1=val1'), request_method='POST',
            response_body='POST MOCK', response_code=400, response_headers={'Content-Type': 'text/plain'}
        )

        response = self.fetch('/simple_fetch')
        self.assertEqual(response.body, b'400 : text/plain : POST MOCK')

    def test_mock_response_file_xml(self):
        patch_http_client(self.app_http_client)

        set_stub(
            self.app_http_client, self.get_url('/simple_fetch?arg1=val1&arg2=val2'), request_method='POST',
            response_file='tests/response_stub.xml', response_code=400
        )

        response = self.fetch('/simple_fetch')
        self.assertEqual(response.body, b'400 : application/xml : <response>$data_tpl</response>')

    def test_mock_response_body_processor(self):
        patch_http_client(self.app_http_client)

        set_stub(
            self.app_http_client, self.get_url('/simple_fetch?arg1=$val_tpl'), request_method='POST',
            response_file='tests/response_stub.xml', response_code=400,
            val_tpl='val1', data_tpl='MOCK DATA'
        )

        response = self.fetch('/simple_fetch')
        self.assertEqual(response.body, b'400 : application/xml : <response>MOCK DATA</response>')

    def test_mock_response_body_no_processor(self):
        patch_http_client(self.app_http_client)

        set_stub(
            self.app_http_client, self.get_url('/simple_fetch?arg1=$val_tpl'), request_method='POST',
            response_file='tests/response_stub.xml', response_code=400, response_body_processor=None,
            val_tpl='val1', data_tpl='MOCK DATA'
        )

        response = self.fetch('/simple_fetch')
        self.assertEqual(response.body, b'400 : application/xml : <response>$data_tpl</response>')

    def test_mock_response_function(self):
        patch_http_client(self.app_http_client)

        def _response_function(request):
            return get_response_stub(
                request, code=404, buffer='RESPONSE FUNCTION', headers={'Content-Type': 'text/plain'}
            )

        set_stub(
            self.app_http_client, self.get_url('/simple_fetch'), request_method='POST',
            response_function=_response_function
        )

        response = self.fetch('/simple_fetch')
        self.assertEqual(response.body, b'404 : text/plain : RESPONSE FUNCTION')

    def test_mock_response_file_json(self):
        patch_http_client(self.app_http_client)

        set_stub(
            self.app_http_client, self.get_url('/simple_fetch'), request_method='POST',
            response_file='tests/response_stub.json', response_code=400,
            data_tpl='MOCK DATA'
        )

        response = self.fetch('/simple_fetch')
        self.assertEqual(response.body, b'400 : application/json : {"response": "MOCK DATA"}')

    def test_mock_response_file_other(self):
        patch_http_client(self.app_http_client)

        set_stub(
            self.app_http_client, self.get_url('/simple_fetch'), request_method='POST',
            response_file='tests/response_stub.txt', response_code=401,
            data_tpl='MOCK DATA'
        )

        response = self.fetch('/simple_fetch')
        self.assertEqual(response.body, b'401 : RESPONSE : MOCK DATA')

    def test_identical_mocks(self):
        patch_http_client(self.app_http_client)

        set_stub(
            self.app_http_client, self.get_url('/simple_fetch'), request_method='POST',
            response_body='FIRST'
        )

        set_stub(
            self.app_http_client, self.get_url('/simple_fetch'), request_method='POST',
            response_body='SECOND'
        )

        response = self.fetch('/simple_fetch')
        self.assertEqual(response.body, b'200 : SECOND')


class SimpleAsyncHTTPClientMockTest(_BaseHTTPClientMockTest):
    def get_app_http_client(self):
        AsyncHTTPClient.configure('tornado.simple_httpclient.SimpleAsyncHTTPClient')
        return AsyncHTTPClient(force_instance=True)


class CurlAsyncHTTPClientMockTest(_BaseHTTPClientMockTest):
    def get_app_http_client(self):
        AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient')
        return AsyncHTTPClient(force_instance=True)
