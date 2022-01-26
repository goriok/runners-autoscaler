import subprocess
from collections import namedtuple
from json.decoder import JSONDecodeError
from unittest import TestCase, mock

import pytest
import requests
from autoscaler.clients.base import (BaseAPIService, BaseSubprocessAPIService,
                                     BearerAuth)
from autoscaler.core.exceptions import PipesHTTPError
from tests.helpers import capture_output


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

        with self.assertRaises(PipesHTTPError):
            BaseAPIService().make_http_request('http://fake_url',)

        response_object.json.side_effect = JSONDecodeError('Error decoding string', *('', 0))
        data, status = BaseAPIService().make_http_request('http://fake_url', ignore_exc=(404, ))
        self.assertEqual(status, 404)
        self.assertEqual(data, '')


class BaseSubprocessAPIServiceTestCase(TestCase):

    @mock.patch('subprocess.run')
    def test_run_command_fail(self, subprocess_mock):
        subprocess_mock.side_effect = subprocess.CalledProcessError(cmd='test', returncode=1)
        service = BaseSubprocessAPIService()
        with capture_output() as out:
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                service.run_command('test')

        self.assertEqual(pytest_wrapped_e.type, SystemExit)
        self.assertIn('Return code: 1', out.getvalue())

    @mock.patch('autoscaler.clients.base.Popen')
    def test_run_piped_command_fail(self, subprocess_mock):
        process_mock = mock.Mock()
        attrs = {'communicate.return_value': ('output', 'error')}
        process_mock.configure_mock(**attrs)
        subprocess_mock.return_value = process_mock
        subprocess_mock.return_value.returncode = 1
        service = BaseSubprocessAPIService()
        with capture_output() as out:
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                service.run_piped_command('test1 apply -foo', 'test2 apply -bar')

        self.assertTrue(subprocess_mock.called)
        self.assertEqual(pytest_wrapped_e.type, SystemExit)
        self.assertIn('Subprocess: Return code for command: 1', out.getvalue())

    @mock.patch('autoscaler.clients.base.Popen')
    def test_run_piped_command_success(self, subprocess_mock):
        process_mock = mock.Mock()
        attrs = {'communicate.return_value': ('output', 'text')}
        process_mock.configure_mock(**attrs)
        subprocess_mock.return_value = process_mock
        subprocess_mock.return_value.returncode = 0
        service = BaseSubprocessAPIService()
        result = service.run_piped_command('test1 apply -foo', 'test2 apply -bar')

        self.assertTrue(subprocess_mock.called)
        self.assertIn('output', result)
