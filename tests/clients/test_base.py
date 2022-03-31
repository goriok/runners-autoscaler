from collections import namedtuple
from json.decoder import JSONDecodeError
from unittest import TestCase, mock

import requests

from autoscaler.clients.base import BaseAPIService, BearerAuth
from autoscaler.core.exceptions import AutoscalerHTTPError


class BearerAuthTestCase(TestCase):

    def test_bearer_auth(self):
        auth = BearerAuth('mytoken')
        request = namedtuple('Request', ('headers', ))
        request.headers = {}
        auth(request)
        self.assertEqual(request.headers['Authorization'], 'Bearer mytoken')


class BaseAPIServiceTestCase(TestCase):

    @mock.patch('requests.request')
    def test_make_http_request(self, mock_request):
        response_object = mock.MagicMock(status_code=201)
        response_object.json.return_value = {'key': 'value'}

        mock_request.return_value.__enter__.return_value = response_object
        data, status = BaseAPIService().make_http_request('http://fake_url', method='post', json={'key': 'value'},
                                                          headers={'Content-Application': 'json'})
        self.assertEqual(status, 201)
        self.assertEqual(data, {'key': 'value'})
        mock_request.assert_called_once_with('post', 'http://fake_url', auth=mock.ANY, json={'key': 'value'},
                                             headers={'Content-Application': 'json'},
                                             timeout=5)

    @mock.patch('requests.request')
    def test_make_http_request_not_found(self, mock_request):
        response_object = mock.MagicMock(status_code=404, text='')
        response_object.raise_for_status.side_effect = requests.exceptions.HTTPError

        mock_request.return_value.__enter__.return_value = response_object

        with self.assertRaises(AutoscalerHTTPError):
            BaseAPIService().make_http_request('http://fake_url',)

        response_object.json.side_effect = JSONDecodeError('Error decoding string', *('', 0))
        data, status = BaseAPIService().make_http_request('http://fake_url', ignore_exc=(404, ))
        self.assertEqual(status, 404)
        self.assertEqual(data, '')
